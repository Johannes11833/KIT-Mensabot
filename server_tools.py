from typing import Dict

import requests
from telegram.ext import CallbackContext

import callback_keyboards as keyboards
import keys as keys
from callback_type import CallbackType
from day import Day
from meal import Meal


def get_user_selected_canteen(context: CallbackContext = None, chat_data: Dict = None):
    assert not (context is None and chat_data is None)

    if chat_data is not None:
        return chat_data.get(keys.CHAT_DATA_KEY_SELECTED_CANTEEN, Day.CANTEEN_KEY_ADENAUER)
    else:
        return context.chat_data.get(keys.CHAT_DATA_KEY_SELECTED_CANTEEN, Day.CANTEEN_KEY_ADENAUER)


def set_canteen(context: CallbackContext, operation):
    keyboard = keyboards.get_callback_keyboard(callback_type=CallbackType.selected_canteen,
                                               data=list(Day.CANTEEN_NAMES.keys()),
                                               action_text=list(Day.CANTEEN_NAMES.values()),
                                               one_per_row=True
                                               )

    current = Day.get_name_of(get_user_selected_canteen(context=context))
    operation(text=f'Aktuell ausgewählt: <strong>{current}</strong> \n\nMensa ändern:',
              reply_markup=keyboard, parse_mode='HTML')


def get_meme(subreddit: str = None) -> Dict:
    if subreddit is not None:
        resp = requests.get(url=f'https://meme-api.herokuapp.com/gimme/{subreddit}')
    else:
        resp = requests.get(url='https://meme-api.herokuapp.com/gimme')
    return resp.json()


def get_pricegroup(chat_data: Dict) -> str:
    return chat_data.get(keys.CHAT_DATA_KEY_SELECTED_PRICE_GROUP, Meal.KEY_NAME_PRICE)
