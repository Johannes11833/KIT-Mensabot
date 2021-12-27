from datetime import datetime
from typing import Dict, List

import canteen_properties as props
from mensa_queue import Queue


def remove_suffix(string: str, suffix: str) -> str:
    if string.endswith(suffix):
        return string[:-len(suffix)]
    else:
        return string


class CanteenDay:

    def __init__(self, canteen_key: str, data: dict, date: datetime) -> None:
        self.date: datetime = date
        self.canteen_key = canteen_key
        self.queue_dict: Dict[str, Queue] = {}

        for q_key, q_name in props.QUEUE_NAMES[canteen_key].items():
            self.queue_dict[q_key] = Queue(q_name, data[q_key])

    def get_list(self) -> List[Queue]:
        return list(self.queue_dict.values())

    def get_name(self):
        return props.CANTEEN_NAMES[self.canteen_key]

    @staticmethod
    def get_name_of(key):
        return props.CANTEEN_NAMES[key]

    @staticmethod
    def get_canteen_names() -> List:
        return list(props.CANTEEN_NAMES.values())

    @staticmethod
    def get_canteen_keys() -> List:
        return list(props.CANTEEN_NAMES.keys())

    def __str__(self) -> str:
        out = f'<{self.date.__str__()}: '
        for q_key, value in self.queue_dict.items():
            out += f'{value.name}: {[meal.__str__() for meal in self.queue_dict[q_key].meals]}, '

        # remove ', ' suffix
        out = remove_suffix(out, ', ')

        out += '>'
        return out
