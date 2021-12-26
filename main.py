import json
import logging
import pathlib
from datetime import datetime
from enum import Enum
from typing import Union, Dict, Set

import pytz
import requests
from telegram import Update, CallbackQuery
from telegram.ext import Updater, CommandHandler, CallbackContext, PicklePersistence, CallbackQueryHandler, Dispatcher

import callback_keyboards as keyboards
from day import Day
from meal import Meal
from scheduler import TimeScheduler, Task

CHAT_DATA_KEY_SELECTED_CANTEEN = 'user_selected_canteen'
CHAT_DATA_KEY_SELECTED_PRICE_GROUP = 'user_selected_price_group'
BOT_DATA_KEY_PUSH_REGISTER = 'push_notification_uids'


class CallbackType(Enum):
    selected_date = 'selected_date'
    selected_canteen = 'selected_canteen'
    reselect_canteen = 'select_another_canteen'
    selected_show_menu = 'show_menu'
    selected_set_price_group = 'selected_set_price_group'


class Server:

    def __init__(self, server_config: Dict) -> None:
        super().__init__()
        self.server_config = server_config

        # cache the json data
        self.canteen_data: Dict = {}

        self.updater: Union[Updater, None] = None

        self.logger: Union[logging.Logger, None] = None

    # api call handlers
    @staticmethod
    def set_canteen(update, _):
        keyboard = keyboards.get_callback_keyboard(callback_type=CallbackType.selected_canteen,
                                                   data=list(Day.CANTEEN_NAMES.keys()),
                                                   action_text=list(Day.CANTEEN_NAMES.values()),
                                                   one_per_row=True
                                                   )
        update.message.reply_text('Wähle ein Mensa aus:', reply_markup=keyboard)

    def get_mensa_plan(self, update: Union[Update, CallbackQuery], context: CallbackContext):
        out = self._get_reply_text(context.chat_data)

        keyboard = keyboards.get_select_dates_keyboard(
            days=self.canteen_data[self.get_user_selected_canteen(context=context)])
        update.message.reply_text(out, parse_mode='HTML', reply_markup=keyboard)

    def get_mensa_plan_all(self, update: Union[Update, CallbackQuery], context: CallbackContext):
        out = 'Alle derzeit verfügbaren Tage:'

        keyboard = keyboards.get_select_dates_keyboard(
            days=self.canteen_data[self.get_user_selected_canteen(context=context)],
            show_all=True)
        update.message.reply_text(out, parse_mode='HTML', reply_markup=keyboard)

    @staticmethod
    def start(update, _):
        update.message.reply_text(
            'Moin Meister! '
            'Ich bin ein Bot, der dir den aktuellen Speiseplan der Mensen in Karlsruhe anzeigen kann. '
            '\n\nGebe /mensa ein, um loszulegen.')

    @staticmethod
    def push_register(update: Update, context: CallbackContext):
        register: Set = context.bot_data[BOT_DATA_KEY_PUSH_REGISTER]

        chat_id = update.message.chat_id
        if chat_id not in register:
            register.add(chat_id)
            update.message.reply_text('Automatische Benachrichtigungen wurden aktiviert ✅')
        else:
            register.remove(chat_id)
            update.message.reply_text('Automatische Benachrichtigungen wurden deaktiviert ❌ '
                                      '\nDu wirst keine automatischen Updates mehr bekommen.')

    @staticmethod
    def set_price_group(update: Update, _):
        keyboard = keyboards.get_callback_keyboard(callback_type=CallbackType.selected_set_price_group,
                                                   data=Meal.get_price_group_keys(),
                                                   action_text=Meal.get_price_group_names(),
                                                   one_per_row=True
                                                   )
        update.message.reply_text('Wähle eine Preisgruppe aus:', reply_markup=keyboard)

    def error(self, update, context):
        """Log Errors caused by Updates."""
        self.logger.warning('Update "%s" caused error "%s"', update, context.error)

    @staticmethod
    def get_user_selected_canteen(context: CallbackContext = None, chat_data: Dict = None):
        assert not (context is None and chat_data is None)

        if chat_data is not None:
            return chat_data.get(CHAT_DATA_KEY_SELECTED_CANTEEN, Day.CANTEEN_KEY_ADENAUER)
        else:
            return context.chat_data.get(CHAT_DATA_KEY_SELECTED_CANTEEN, Day.CANTEEN_KEY_ADENAUER)

    def _send_menu_push_notifications(self):
        if datetime.now().strftime('%d.%m.%Y') in self.canteen_data.keys():
            self.logger.info('sending push')
            dp: Dispatcher = self.updater.dispatcher
            chat_ids = dp.bot_data[BOT_DATA_KEY_PUSH_REGISTER]

            for c_id in chat_ids:
                chat_data = dp.chat_data[c_id]
                selected_canteen_id = self.get_user_selected_canteen(chat_data=chat_data)
                keyboard = keyboards.get_select_dates_keyboard(days=self.canteen_data[selected_canteen_id])

                self.updater.bot.send_message(c_id, self._get_reply_text(chat_data),
                                              parse_mode='HTML', reply_markup=keyboard)
        else:
            self.logger.info('no data available for today. not sending push')

    def start_server(self):
        # create Data folder and initialize PicklePersistence of the bot's data
        pathlib.Path('./data').mkdir(exist_ok=True)
        persistence = PicklePersistence('./data/bot_data.pkl')

        # setup logger
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO,
                            handlers=[
                                logging.FileHandler("data/server_log.log"),
                                logging.StreamHandler()
                            ])
        self.logger = logging.getLogger(__name__)

        # get the token
        with open('data/config.json') as json_file:
            telegram_token = json.load(json_file)['telegram_token']

        # fetch the data
        self._fetch_mensa_menu()

        """Start the bot."""
        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary
        self.updater = Updater(telegram_token, use_context=True, persistence=persistence)

        # Get the dispatcher to register handlers
        dp = self.updater.dispatcher

        # Create the push subscriber register
        if BOT_DATA_KEY_PUSH_REGISTER not in dp.bot_data.keys():
            # use a set to store the chat ids so every id can only exist once in ti
            dp.bot_data[BOT_DATA_KEY_PUSH_REGISTER] = set()

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("menu", self.get_mensa_plan))
        dp.add_handler(CommandHandler("menu_all", self.get_mensa_plan_all))
        dp.add_handler(CommandHandler("mensa", self.set_canteen))
        dp.add_handler(CommandHandler("push", self.push_register))
        dp.add_handler(CommandHandler("price", self.set_price_group))
        dp.add_handler(CallbackQueryHandler(self.callbacks))  # handling inline buttons pressing

        # log all errors
        dp.add_error_handler(self.error)

        # Start the Bot
        self.updater.start_polling()

        # schedule data refresh and push notifications
        ts = TimeScheduler()
        ts.add(Task(self.server_config.get('push_notification_time', '09:00'), self._send_menu_push_notifications))
        ts.add(Task(self.server_config.get('data_refresh_time', '03:00'), self._fetch_mensa_menu))
        ts.start()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()

    def _fetch_mensa_menu(self):
        self.logger.info('refreshing data...')
        tmp_canteen_data = {}

        supported_canteens = Day.QUEUE_NAMES.keys()

        for canteen_key in supported_canteens:

            r = requests.get(f'https://www.sw-ka.de/json_interface/canteen/?mensa[]={canteen_key}',
                             auth=(self.server_config['api_user_name'], self.server_config['api_password']))

            if r.status_code == 200:
                result: dict = r.json()[canteen_key]

                days_dict: Dict[str, Day] = {}

                # iterate over the days
                for date_unix, day_json in result.items():
                    # mensa uses (weird) local timestamp
                    timestamp = datetime.fromtimestamp(int(date_unix), pytz.timezone('Europe/Berlin'))

                    day = Day(canteen_key, day_json, timestamp)
                    days_dict[timestamp.strftime('%d.%m.%Y')] = day

                tmp_canteen_data[canteen_key] = days_dict
            else:
                # no valid data
                tmp_canteen_data[canteen_key] = None

        self.canteen_data = tmp_canteen_data

    def _get_reply_text(self, chat_data: dict, timestamp: datetime = None) -> Union[str, None]:
        timestamp = (timestamp if timestamp else datetime.now()).strftime('%d.%m.%Y')

        selected_canteen = self.get_user_selected_canteen(chat_data=chat_data)

        days_dict = self.canteen_data[selected_canteen]
        if days_dict is not None and timestamp in days_dict.keys():
            canteen_day: Day = days_dict[timestamp]
            out: str = f'Speiseplan der {canteen_day.get_name()} am <strong>{timestamp}</strong>:\n\n'

            for queue in days_dict[timestamp].get_list():
                if not queue.closed:
                    # queue name
                    out += f'<strong>{queue.name}</strong>\n'

                    # meals
                    for meal in queue.meals:
                        out += f'•{meal.meal_name}'

                        price = meal.get_price(chat_data.get(CHAT_DATA_KEY_SELECTED_PRICE_GROUP, None))
                        if price != 0:
                            out += ': <u>{:,.2f}€</u>'.format(price)

                        if meal.dish_description:
                            out += f' (<i>{meal.dish_description}</i>)'
                        out += '\n'
                else:
                    # queue is closed on this day
                    out += f'<strong>{queue.name}</strong> - geschlossen\n'
                out += '\n'
            return out
        else:
            return f'👾 Für den <strong> {timestamp}</strong> gibt es noch keinen Mensa Plan ' \
                   f'({Day.CANTEEN_NAMES[selected_canteen]}) 👾'

    def callbacks(self, update, context: CallbackContext):
        """
        callback method the selection of a day
        """
        # getting the callback query
        query: CallbackQuery = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        query.answer()

        query_data_dict = json.loads(query.data)

        callback_type = CallbackType(query_data_dict['type'])
        data = query_data_dict['data']

        if callback_type is CallbackType.selected_date:
            selected_canteen = self.get_user_selected_canteen(context=context)

            timestamp = datetime.strptime(data, '%d.%m.%Y')
            out = self._get_reply_text(context.chat_data, timestamp=timestamp)

            # edit the message previously sent by the bot
            keyboard = keyboards.get_select_dates_keyboard(
                days=self.canteen_data[selected_canteen])
            query.edit_message_text(text=out, parse_mode='HTML', reply_markup=keyboard)
        elif callback_type is CallbackType.selected_canteen:
            context.chat_data[CHAT_DATA_KEY_SELECTED_CANTEEN] = data
            query.edit_message_text(text=f'<strong>{Day.CANTEEN_NAMES[data]}</strong> wurde ausgewählt.',
                                    parse_mode='HTML',
                                    reply_markup=keyboards.get_callback_keyboard(
                                        [CallbackType.selected_show_menu, CallbackType.reselect_canteen],
                                        [None, None],
                                        ['Speiseplan anzeigen',
                                         'Andere Mensa wählen']))
        elif callback_type is CallbackType.reselect_canteen:
            self.set_canteen(query, context)
        elif callback_type is CallbackType.selected_set_price_group:
            context.chat_data[CHAT_DATA_KEY_SELECTED_PRICE_GROUP] = data

            query.edit_message_text(f'Preisgruppe <strong>{Meal.get_price_group(data)}</strong> wurde ausgewählt.',
                                    parse_mode='HTML')
        else:
            # show the menu by default
            self.get_mensa_plan(query, context)


if __name__ == '__main__':
    with open('./data/config.json', 'r') as fh:
        config = json.load(fh)

        server = Server(config)
        server.start_server()
