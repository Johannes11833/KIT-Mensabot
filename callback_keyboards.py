import json
from datetime import datetime, timedelta
from typing import List, Dict, Union

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


def get_callback_keyboard(callback_type: Union[CallbackType, List[CallbackType]], data: List, action_text: List,
                          one_per_row=False):
    keyboard = []

    is_type_list = isinstance(callback_type, list) or isinstance(callback_type, tuple)
    for index in range(0, len(action_text)):
        d_type_str = callback_type[index].value if is_type_list else callback_type.value
        keyboard.append(
            InlineKeyboardButton(action_text[index],
                                 callback_data=json.dumps({'type': d_type_str, 'data': data[index]})), )

    if not one_per_row:
        return InlineKeyboardMarkup([keyboard])
    else:
        return InlineKeyboardMarkup([[item] for item in keyboard])
