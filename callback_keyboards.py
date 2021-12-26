import json
from datetime import datetime, timedelta
from typing import List, Dict, Union

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from main import CallbackType


def _german_weekday_name(name: str):
    translations = {'Mon': 'Mo', 'Tue': 'Di', 'Wed': 'Mi', 'Thu': 'Do', 'Fri': 'Fr'}

    if name in translations.keys():
        return translations[name]
    else:
        return name


def get_select_dates_keyboard(days: Dict, show_all=False) -> InlineKeyboardMarkup:
    count = 0
    delta_t = 0
    data = []
    action_text = []
    timestamps = list(days.keys())

    max_selections = 5
    while count < max_selections or show_all:
        ts_i = datetime.now() + timedelta(days=delta_t)
        ts_i_str = (datetime.now() + timedelta(days=delta_t)).strftime('%d.%m.%Y')

        if ts_i > datetime.strptime(timestamps[-1], '%d.%m.%Y'):
            # the current timestamp is larger than the last provided by the api.
            break

        if ts_i_str in timestamps:
            count += 1
            if show_all:
                # when showing all, always use the dates
                name = ts_i.strftime('%d.%m')
            elif delta_t == 0:
                name = 'Heute'
            elif delta_t == 1:
                name = 'Morgen'
            elif delta_t < 7:
                name = _german_weekday_name(ts_i.strftime('%a'))
            else:
                name = ts_i.strftime('%d.%m')

            data.append(ts_i_str)
            action_text.append(name)

        delta_t += 1

    return get_callback_keyboard(callback_type=CallbackType.selected_date,
                                 data=data,
                                 action_text=action_text,
                                 max_per_row=3 if show_all else None
                                 )


def get_callback_keyboard(callback_type: Union[CallbackType, List[CallbackType]], data: List, action_text: List,
                          one_per_row=False, max_per_row=None):
    keyboard = []

    is_type_list = isinstance(callback_type, list) or isinstance(callback_type, tuple)
    for index in range(0, len(action_text)):
        d_type_str = callback_type[index].value if is_type_list else callback_type.value
        keyboard.append(
            InlineKeyboardButton(action_text[index],
                                 callback_data=json.dumps({'type': d_type_str, 'data': data[index]})), )

    if one_per_row:
        return InlineKeyboardMarkup([[item] for item in keyboard])
    elif max_per_row is not None:
        # reshape keyboard to 2d with max_per_row items per row
        count = 0
        out = []
        for b in keyboard:
            index = count // max_per_row

            (out[index].append(b)) if len(out) > index else (out.append([b]))
            count += 1
        return InlineKeyboardMarkup(out)
    else:
        return InlineKeyboardMarkup([keyboard])
