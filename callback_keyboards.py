import json
from datetime import datetime, timedelta
from typing import List

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from main import CallbackType


def get_select_dates_keyboard() -> InlineKeyboardMarkup:
    # add callbacks
    now_str = datetime.now().strftime('%d.%m.%Y')
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
    day_after_tomorrow_str = (datetime.now() + timedelta(days=2)).strftime('%d.%m.%Y')

    return get_callback_keyboard(callback_type=CallbackType.selected_date,
                                 data=[now_str, tomorrow_str, day_after_tomorrow_str],
                                 action_text=['heute', 'morgen', 'übermorgen']
                                 )


def get_callback_keyboard(callback_type: CallbackType, data: List, action_text: List):
    keyboard = []
    for d, a in zip(data, action_text):
        keyboard.append(
            InlineKeyboardButton(a, callback_data=json.dumps({'type': callback_type.value, 'data': d})), )

    return InlineKeyboardMarkup([keyboard])
