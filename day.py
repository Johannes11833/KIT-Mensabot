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
    CANTEEN_KEY_ERZBERGER = 'erzberger'
    CANTEEN_KEY_GOTTESAUE = 'gottesaue'
    CANTEEN_KEY_HOLZGARTEN = 'holzgarten'
    CANTEEN_KEY_PFORZHEIM = 'tiefenbronner'

    QUEUE_NAMES = {
        CANTEEN_KEY_ADENAUER: {
            'l1': 'Linie 1',
            'l2': 'Linie 2',
            'l3': 'Linie 3',
            'l45': 'Linie 4',
            'l5': 'Linie 5',
            'update': 'L6 Update',
            'schnitzelbar': 'Schnitzelbar',
            'pizza': '[pizza]werk Pizza',
            'pasta': '[pizza]werk Pasta',
            'aktion': '[kœri]werk',
        },
        CANTEEN_KEY_MOLTKE: {
            'gut': 'Gut & Günstig'
        }, CANTEEN_KEY_ERZBERGER: {
            'wahl1': 'Wahlessen 1',
            'wahl2': 'Wahlessen 2',
            'wahl3': 'Wahlessen 3'
        }, CANTEEN_KEY_GOTTESAUE: {
            'wahl1': 'Wahlessen 1',
            'wahl2': 'Wahlessen 2'
        }, CANTEEN_KEY_HOLZGARTEN: {
            'gut': 'Gut & Günstig 1',
            'gut2': 'Gut & Günstig 2'
        }, CANTEEN_KEY_PFORZHEIM: {
            'wahl1': 'Wahlessen 1',
            'wahl2': 'Wahlessen 2',
            'gut': 'Gut & Günstig',
            'buffet': 'Buffet'
        }
    }

    CANTEEN_NAMES = {
        CANTEEN_KEY_ADENAUER: 'Mensa am Adenauer Ring',
        CANTEEN_KEY_MOLTKE: 'Mensa Moltkestraße',
        CANTEEN_KEY_ERZBERGER: 'Mensa Erzbergerstraße',
        CANTEEN_KEY_GOTTESAUE: 'Mensa Schloss Gottesaue',
        CANTEEN_KEY_HOLZGARTEN: 'Mensa I Holzgartenstraße (Stuttgart-Mitte)',
        CANTEEN_KEY_PFORZHEIM: 'Mensa Fachhochschule Pforzheim'
    }

    def __init__(self, canteen_key: str, data: dict, date: datetime) -> None:
        self.date: datetime = date
        self.canteen_key = canteen_key
        self.queue_dict: Dict[str, Queue] = {}

        for q_key, q_name in self.QUEUE_NAMES[canteen_key].items():
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
