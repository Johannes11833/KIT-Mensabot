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
        self._canteen_closed = True

        for q_key, q_name in props.QUEUE_NAMES[canteen_key].items():
            if q_key in data.keys():
                q = Queue(q_name, data[q_key])
                self.queue_dict[q_key] = q

                if not q.closed:
                    self._canteen_closed = False

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
    def get_canteen_names_short() -> List:
        return list(props.CANTEEN_NAMES_SHORT.values())

    @staticmethod
    def get_canteen_keys() -> List:
        return list(props.CANTEEN_NAMES.keys())

    def get_canteen_closed(self):

        return self._canteen_closed

    def __str__(self) -> str:
        out = f'<{self.date.__str__()}: '
        for q_key, value in self.queue_dict.items():
            out += f'{value.name}: {[meal.__str__() for meal in self.queue_dict[q_key].meals]}, '

        # remove ', ' suffix
        out = remove_suffix(out, ', ')

        out += '>'
        return out
