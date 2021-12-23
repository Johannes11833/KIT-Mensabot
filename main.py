import json
import logging
import pathlib
from datetime import datetime
from enum import Enum
from typing import Union, Dict

import pytz
import requests
from telegram import Update, CallbackQuery
from telegram.ext import Updater, CommandHandler, CallbackContext, PicklePersistence, \
    CallbackQueryHandler

import callback_keyboards as keyboards
from day import Day

USER_DATA_KEY_SELECTED_CANTEEN = 'user_selected_canteen'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class CallbackType(Enum):
    selected_date = 'selected_date'
    selected_canteen = 'selected_canteen'
    show_menu = 'show_menu'


class Server:

    def __init__(self, server_config: Dict) -> None:
        super().__init__()
        self.server_config = server_config

        # cache the json data
        self.canteen_data: Dict = {}

    @staticmethod
    def set_canteen(update, _):
        keyboard = keyboards.get_callback_keyboard(callback_type=CallbackType.selected_canteen,
                                                   data=Day.CANTEEN_NAMES.keys(),
                                                   action_text=Day.CANTEEN_NAMES.values()
                                                   )
        update.message.reply_text('Wähle ein Mensa aus:', reply_markup=keyboard)

    @staticmethod
    def get_user_selected_canteen(context: CallbackContext):
        return context.user_data.get(USER_DATA_KEY_SELECTED_CANTEEN, Day.CANTEEN_KEY_MOLTKE)

    @staticmethod
    def start(update, _):
        update.message.reply_text(
            'Moin Meister! Ich bin ein Bot, der dir den aktuellen Mensaplan des KITs anzeigen kann.'
            ' \n\nGebe /mensa ein, um loszulegen.')

    @staticmethod
    def error(update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    def start_server(self):
        self.canteen_data = self.fetch_mensa_menu()

        # create Data folder and initialize PicklePersistence of the bot's data
        pathlib.Path('./data').mkdir(exist_ok=True)
        persistence = PicklePersistence('./data/bot_data.pkl')

        # get the token
        with open('data/config.json') as json_file:
            telegram_token = json.load(json_file)['telegram_token']

        """Start the bot."""
        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary
        updater = Updater(telegram_token, use_context=True, persistence=persistence)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("mensa", self.get_mensa_plan))
        dp.add_handler(CommandHandler("set_mensa", self.set_canteen))
        dp.add_handler(CallbackQueryHandler(self.callbacks))  # handling inline buttons pressing

        # log all errors
        dp.add_error_handler(self.error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()

    def fetch_mensa_menu(self) -> Dict:
        tmp_canteen_data = {}

        supported_canteens = Day.QUEUE_PROPERTIES.keys()

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

        return tmp_canteen_data

    def get_reply_text(self, timestamp: datetime, selected_canteen: str) -> Union[str, None]:
        timestamp = timestamp.strftime('%d.%m.%Y')

        days_dict = self.canteen_data[selected_canteen]
        if days_dict is not None and timestamp in days_dict.keys():
            canteen_day: Day = days_dict[timestamp]
            out: str = f'Menu der {canteen_day.get_name()} am <strong>{timestamp}</strong>:\n\n'

            for queue in days_dict[timestamp].get_list():
                if not queue.closed:
                    # queue name
                    out += f'<strong>{queue.name}</strong>\n'

                    # meals
                    for meal in queue.meals:
                        out += f'•{meal.meal_name}'
                        if meal.price != 0:
                            out += ': <u>{:,.2f}€</u>'.format(meal.price)

                        if meal.dish_description:
                            out += f' (<i>{meal.dish_description}</i>)'
                        out += '\n'
                else:
                    # queue is closed on this day
                    out += f'<strong>{queue.name}</strong> - geschlossen\n'
                out += '\n'
            return out
        else:
            return f'👾 Für den <strong> {timestamp}</strong> gibt es noch keinen Mensa Plan. 👾'

    def get_mensa_plan(self, update: Union[Update, CallbackQuery], context: CallbackContext):
        out = self.get_reply_text(datetime.now(tz=pytz.timezone('Europe/Berlin')),
                                  self.get_user_selected_canteen(context))

        update.message.reply_text(out, parse_mode='HTML', reply_markup=keyboards.get_select_dates_keyboard())

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

            timestamp = datetime.strptime(data, '%d.%m.%Y')
            out = self.get_reply_text(timestamp, self.get_user_selected_canteen(context))

            # edit the message previously sent by the bot
            query.edit_message_text(text=out, parse_mode='HTML', reply_markup=keyboards.get_select_dates_keyboard())
        elif callback_type is CallbackType.selected_canteen:
            context.user_data[USER_DATA_KEY_SELECTED_CANTEEN] = data
            query.edit_message_text(text=f'<strong>{Day.CANTEEN_NAMES[data]}</strong> wurde ausgewählt.',
                                    parse_mode='HTML',
                                    reply_markup=keyboards.get_callback_keyboard(CallbackType.show_menu, ['show_menu'],
                                                                                 ['Show Menu']))
        else:
            # show the menu
            self.get_mensa_plan(query, context)


if __name__ == '__main__':
    with open('./data/config.json', 'r') as fh:
        config = json.load(fh)

        server = Server(config)
        server.start_server()
