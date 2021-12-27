import json
import logging
import pathlib
from datetime import datetime
from typing import Union, Dict, Set

from telegram import Update, CallbackQuery
from telegram.ext import Updater, CommandHandler, CallbackContext, PicklePersistence, CallbackQueryHandler, Dispatcher

import callback_keyboards as keyboards
import keys as keys
import server_tools as server_tools
from callback_type import CallbackType
from canteenday import CanteenDay
from meal import Meal
from scheduler import TimeScheduler, Task
from server_data import ServerData


class Server:

    def __init__(self, server_config: Dict) -> None:
        super().__init__()
        self.server_config = server_config

        # cache the json data
        self.server_data: Union[ServerData, None] = None

        self.updater: Union[Updater, None] = None

        self.logger: Union[logging.Logger, None] = None

    # api call handlers
    @staticmethod
    def set_canteen(update, context):
        server_tools.set_canteen(context, update.message.reply_text)

    def get_mensa_plan(self, update: Union[Update, CallbackQuery], context: CallbackContext):
        server_tools.get_canteen_plan(update.message.reply_text, self.server_data, context.chat_data)

    def get_mensa_plan_all(self, update: Union[Update, CallbackQuery], context: CallbackContext):
        out = 'Alle derzeit verfügbaren Tage:'

        selected_canteen = server_tools.get_user_selected_canteen(chat_data=context.chat_data)
        keyboard = keyboards.get_select_dates_keyboard(
            days=self.server_data.get_canteen(selected_canteen),
            show_all=True)
        update.message.reply_text(out, parse_mode='HTML', reply_markup=keyboard)

    @staticmethod
    def start(update, _):
        all_canteens = CanteenDay.get_canteen_names().__str__().replace("'", "").replace('[', '').replace(']', '')

        update.message.reply_text(
            'Moin Meister! '
            'Ich bin ein Bot, der dir den aktuellen Speiseplan der Mensen in Karlsruhe anzeigen kann. '
            '\n\n🏠 <strong>Unterstützte Mensen</strong>'
            f"\n{all_canteens}"
            '\n\n⚙️ <strong>Konfiguration</strong>'
            '\n• /mensa legt die zu verwendende Mensa fest'
            '\n• /price legt die Preisklasse fest. Default ist Student.'
            '\n• /push aktiviert/ deaktiviert automatische Benachrichtigungen'
            '\n\n🎉 <strong>Anderes</strong>'
            '\n• /memes hochwertige, zufällige Memes vom KaIT Subreddit',
            parse_mode='HTML')

    @staticmethod
    def memes(update: Update, _):
        result = server_tools.get_meme(subreddit='KaIT')

        update.message.reply_text(f'Hier ein Post von KaIT:\n\n<a href="{result["postLink"]}">{result["title"]}</a>',
                                  parse_mode='HTML', disable_web_page_preview=True)
        update.message.reply_photo(result['url'])

    @staticmethod
    def push_register(update: Update, context: CallbackContext):
        register: Set = context.bot_data[keys.BOT_DATA_KEY_PUSH_REGISTER]

        chat_id = update.message.chat_id
        if chat_id not in register:
            register.add(chat_id)
            update.message.reply_text('Automatische Benachrichtigungen wurden aktiviert ✅')
        else:
            register.remove(chat_id)
            update.message.reply_text('Automatische Benachrichtigungen wurden deaktiviert ❌ '
                                      '\nDu wirst keine automatischen Updates mehr bekommen.')

    @staticmethod
    def set_price_group(update: Update, context: CallbackContext):
        keyboard = keyboards.get_callback_keyboard(callback_type=CallbackType.selected_set_price_group,
                                                   data=Meal.get_price_group_keys(),
                                                   action_text=Meal.get_price_group_names(),
                                                   one_per_row=True
                                                   )
        current = Meal.get_price_group_name(server_tools.get_pricegroup(context.chat_data))
        update.message.reply_text(f'Aktuell eingestellte Preisgruppe: <strong>{current}</strong>\n\n'
                                  f'Preisgruppe ändern:', reply_markup=keyboard, parse_mode='HTML')

    def error(self, update, context):
        """Log Errors caused by Updates."""
        self.logger.warning('Update "%s" caused error "%s"', update, context.error)

    def _send_menu_push_notifications(self):
        if self.server_data.contains_timestamp(datetime.now()):
            self.logger.info('sending push')
            dp: Dispatcher = self.updater.dispatcher
            chat_ids = dp.bot_data[keys.BOT_DATA_KEY_PUSH_REGISTER]

            for c_id in chat_ids:
                chat_data = dp.chat_data[c_id]

                server_tools.get_canteen_plan(self.updater.bot.send_message, self.server_data, chat_data,
                                              chat_id=c_id)
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
        telegram_token = self.server_config['telegram_token']

        # fetch the data
        self.server_data = ServerData(self.logger, self.server_config['api_user_name'],
                                      self.server_config['api_password'])
        self.server_data.fetch_mensa_menu()

        """Start the bot."""
        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary
        self.updater = Updater(telegram_token, use_context=True, persistence=persistence)

        # Get the dispatcher to register handlers
        dp = self.updater.dispatcher

        # Create the push subscriber register
        if keys.BOT_DATA_KEY_PUSH_REGISTER not in dp.bot_data.keys():
            # use a set to store the chat ids so every id can only exist once in ti
            dp.bot_data[keys.BOT_DATA_KEY_PUSH_REGISTER] = set()

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("menu", self.get_mensa_plan))
        dp.add_handler(CommandHandler("menu_all", self.get_mensa_plan_all))
        dp.add_handler(CommandHandler("mensa", self.set_canteen))
        dp.add_handler(CommandHandler("push", self.push_register))
        dp.add_handler(CommandHandler("price", self.set_price_group))
        dp.add_handler(CommandHandler("memes", self.memes))
        dp.add_handler(CallbackQueryHandler(self.callbacks))  # handling inline buttons pressing

        # log all errors
        dp.add_error_handler(self.error)

        # Start the Bot
        self.updater.start_polling()

        # schedule data refresh and push notifications
        ts = TimeScheduler()
        ts.add(Task(self.server_config.get('push_notification_time', '09:00'), self._send_menu_push_notifications))
        ts.add(Task(self.server_config.get('data_refresh_time', '03:00'), self.server_data.fetch_mensa_menu))
        ts.start()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()

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
            timestamp_sel = datetime.strptime(data, '%d.%m.%Y')

            # only update the message if a new date was selected
            prev_date = context.chat_data.get(keys.CHAT_DATA_PREVIOUSLY_SELECTED_DATE, None)
            if prev_date is None or prev_date != data:
                server_tools.get_canteen_plan(query.edit_message_text, self.server_data, context.chat_data,
                                              selected_timestamp=timestamp_sel)

        elif callback_type is CallbackType.selected_canteen:
            context.chat_data[keys.CHAT_DATA_KEY_SELECTED_CANTEEN] = data
            query.edit_message_text(text=f'<strong>{CanteenDay.get_name_of(data)}</strong> wurde ausgewählt.',
                                    parse_mode='HTML',
                                    reply_markup=keyboards.get_callback_keyboard(
                                        [CallbackType.selected_show_menu, CallbackType.reselect_canteen],
                                        [None, None],
                                        ['Speiseplan anzeigen',
                                         'Andere Mensa wählen']))
        elif callback_type is CallbackType.reselect_canteen:
            server_tools.set_canteen(context, query.edit_message_text)
        elif callback_type is CallbackType.selected_set_price_group:
            context.chat_data[keys.CHAT_DATA_KEY_SELECTED_PRICE_GROUP] = data

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
