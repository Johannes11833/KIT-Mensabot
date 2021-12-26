from typing import Dict

import requests
from telegram.ext import CallbackContext

import keys as keys
from day import Day
from meal import Meal


def get_user_selected_canteen(context: CallbackContext = None, chat_data: Dict = None):
    assert not (context is None and chat_data is None)

    if chat_data is not None:
        return chat_data.get(keys.CHAT_DATA_KEY_SELECTED_CANTEEN, Day.CANTEEN_KEY_ADENAUER)
    else:
        return context.chat_data.get(keys.CHAT_DATA_KEY_SELECTED_CANTEEN, Day.CANTEEN_KEY_ADENAUER)


def get_meme(subreddit: str = None) -> Dict:
    if subreddit is not None:
        resp = requests.get(url=f'https://meme-api.herokuapp.com/gimme/{subreddit}')
    else:
        resp = requests.get(url='https://meme-api.herokuapp.com/gimme')
    return resp.json()


def get_pricegroup(chat_data: Dict) -> str:
    return chat_data.get(keys.CHAT_DATA_KEY_SELECTED_PRICE_GROUP, Meal.KEY_NAME_PRICE)
