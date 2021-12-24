import json
from datetime import datetime, timedelta
from typing import List, Dict

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from main import CallbackType


def get_select_dates_keyboard(days: Dict) -> InlineKeyboardMarkup:
    count = 0
    delta_t = 0
    data = []
    action_text = []

    while count < 4:
        timestamp = datetime.now() + timedelta(days=delta_t)
        timestamp_str = (datetime.now() + timedelta(days=delta_t)).strftime('%d.%m.%Y')

        if timestamp_str in days.keys():
            count += 1
            if delta_t == 0:
                name = 'Heute'
            elif delta_t == 1:
                name = 'Morgen'
            elif delta_t < 7:
                name = timestamp.strftime('%a')
            else:
                name = timestamp.strftime('%d.%m')

            data.append(timestamp_str)
            action_text.append(name)

        delta_t += 1

    return get_callback_keyboard(callback_type=CallbackType.selected_date,
                                 data=data,
                                 action_text=action_text
                                 )


def get_callback_keyboard(callback_type: CallbackType, data: List, action_text: List):
    keyboard = []
    for d, a in zip(data, action_text):
        keyboard.append(
            InlineKeyboardButton(a, callback_data=json.dumps({'type': callback_type.value, 'data': d})), )

    return InlineKeyboardMarkup([keyboard])
