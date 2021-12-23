from datetime import datetime
from typing import Dict, List

from mensa_queue import Queue


def remove_suffix(string: str, suffix: str) -> str:
    if string.endswith(suffix):
        return string[:-len(suffix)]
    else:
        return string


class Day:
    # canteen keys
    CANTEEN_KEY_ADENAUER = 'adenauerring'
    CANTEEN_KEY_MOLTKE = 'x1moltkestrasse'

    # adenauer ring
    KEY_QUEUE_L1 = 'l1'
    KEY_QUEUE_L2 = 'l2'
    KEY_QUEUE_L3 = 'l3'
    KEY_QUEUE_L45 = 'l45'
    KEY_QUEUE_L5 = 'l5'
    KEY_QUEUE_SCHNITZEL = 'schnitzelbar'
    KEY_QUEUE_PIZZA = 'pizza'
    KEY_QUEUE_PASTA = 'pasta'
    KEY_QUEUE_KOERI = 'aktion'

    # moltkestraße
    KEY_QUEUE_GUT = 'gut'

    QUEUE_PROPERTIES = {
        CANTEEN_KEY_ADENAUER: {
            KEY_QUEUE_L1: 'Linie 1',
            KEY_QUEUE_L2: 'Linie 2',
            KEY_QUEUE_L3: 'Linie 3',
            KEY_QUEUE_L45: 'Linie 4',
            KEY_QUEUE_L5: 'Linie 5',
            KEY_QUEUE_SCHNITZEL: 'Schnitzelbar',
            KEY_QUEUE_PIZZA: '[pizza]werk Pizza',
            KEY_QUEUE_PASTA: '[pizza]werk Pasta',
            KEY_QUEUE_KOERI: '[kœri]werk',
        },
        CANTEEN_KEY_MOLTKE: {
            KEY_QUEUE_GUT: 'Gut & Günstig'
        }}

    CANTEEN_NAMES = {
        CANTEEN_KEY_ADENAUER: 'Mensa am Adenauer Ring',
        CANTEEN_KEY_MOLTKE: 'Mensa Moltkestraße'
    }

    def __init__(self, canteen_key: str, data: dict, date: datetime) -> None:
        self.date: datetime = date
        self.canteen_key = canteen_key
        self.queue_dict: Dict[str, Queue] = {}

        for q_key, q_name in self.QUEUE_PROPERTIES[canteen_key].items():
            self.queue_dict[q_key] = Queue(q_name, data[q_key])

    def get_list(self) -> List[Queue]:
        return self.queue_dict.values()

    def get_name(self):
        return self.CANTEEN_NAMES[self.canteen_key]

    def __str__(self) -> str:
        out = f'<{self.date.__str__()}: '
        for q_key, value in self.queue_dict.items():
            out += f'{value.name}: {[meal.__str__() for meal in self.queue_dict[q_key].meals]}, '

        # remove ', ' suffix
        out = remove_suffix(out, ', ')

        out += '>'
        return out
