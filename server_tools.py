from datetime import datetime
from typing import Dict

import requests
from telegram.ext import CallbackContext

import callback_keyboards as keyboards
import keys as keys
from callback_type import CallbackType
from day import Day
from meal import Meal


# BOT MESSAGES

def set_canteen(context: CallbackContext, chat_operation):
    keyboard = keyboards.get_callback_keyboard(callback_type=CallbackType.selected_canteen,
                                               data=list(Day.CANTEEN_NAMES.keys()),
                                               action_text=list(Day.CANTEEN_NAMES.values()),
                                               one_per_row=True
                                               )

    current = Day.get_name_of(get_user_selected_canteen(chat_data=context.chat_data))
    chat_operation(text=f'Aktuell ausgewählt: <strong>{current}</strong> \n\nMensa ändern:',
                   reply_markup=keyboard, parse_mode='HTML')


def get_canteen_plan(chat_operation, canteen_data, chat_data: Dict, selected_timestamp: datetime = None, **kwargs):
    selected_timestamp_str = (selected_timestamp if selected_timestamp else datetime.now()).strftime('%d.%m.%Y')

    selected_canteen = get_user_selected_canteen(chat_data=chat_data)

    days_dict = canteen_data[selected_canteen]
    if days_dict is not None and selected_timestamp_str in days_dict.keys():
        canteen_day: Day = days_dict[selected_timestamp_str]
        out: str = f'Speiseplan der {canteen_day.get_name()} am <strong>{selected_timestamp_str}</strong>:\n\n'

        for queue in days_dict[selected_timestamp_str].get_list():
            if not queue.closed:
                # queue name
                out += f'<strong>{queue.name}</strong>\n'

                # meals
                for meal in queue.meals:
                    out += f'•{meal.meal_name}'

                    price = meal.get_price(get_pricegroup(chat_data))
                    if price != 0:
                        out += ': <u>{:,.2f}€</u>'.format(price)

                    if meal.dish_description:
                        out += f' (<i>{meal.dish_description}</i>)'
                    out += '\n'
            else:
                # queue is closed on this day
                out += f'<strong>{queue.name}</strong> - geschlossen\n'
            out += '\n'

            # save the date
            chat_data[keys.CHAT_DATA_PREVIOUSLY_SELECTED_DATE] = selected_timestamp_str
    else:
        out = f'👾 Für den <strong> {selected_timestamp_str}</strong> gibt es noch keinen Mensa Plan ' \
              f'({Day.CANTEEN_NAMES[selected_canteen]}) 👾'

    keyboard = keyboards.get_select_dates_keyboard(
        days=canteen_data[selected_canteen],
    )
    chat_operation(text=out, parse_mode='HTML', reply_markup=keyboard, **kwargs)


# HELPER

def get_user_selected_canteen(chat_data: Dict = None):
    return chat_data.get(keys.CHAT_DATA_KEY_SELECTED_CANTEEN, Day.CANTEEN_KEY_ADENAUER)


def get_meme(subreddit: str = None) -> Dict:
    if subreddit is not None:
        resp = requests.get(url=f'https://meme-api.herokuapp.com/gimme/{subreddit}')
    else:
        resp = requests.get(url='https://meme-api.herokuapp.com/gimme')
    return resp.json()


def get_pricegroup(chat_data: Dict) -> str:
    return chat_data.get(keys.CHAT_DATA_KEY_SELECTED_PRICE_GROUP, Meal.KEY_NAME_PRICE)
