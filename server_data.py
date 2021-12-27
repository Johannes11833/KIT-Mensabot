from datetime import datetime
from typing import Dict

import pytz
import requests

import canteen_properties as props
from canteenday import CanteenDay


class ServerData:

    def __init__(self, logger, user_name, api_password) -> None:
        super().__init__()

        # dict of canteen_key : timestamp : canteen day data
        self._data = {}
        self.logger = logger
        self._api_username = user_name
        self._api_password = api_password

    def fetch_mensa_menu(self):
        self.logger.info('refreshing data...')

        supported_canteens = props.QUEUE_NAMES.keys()

        tmp_canteen_data = {}

        # reformat data to Dict[timestamp][canteen_key] containing canteen data json
        for canteen_key in supported_canteens:

            r = requests.get(f'https://www.sw-ka.de/json_interface/canteen/?mensa[]={canteen_key}',
                             auth=(self._api_username, self._api_password))

            if r.status_code == 200:
                result: dict = r.json()[canteen_key]

                days_dict: Dict[str, CanteenDay] = {}

                # iterate over the days
                for date_unix, day_json in result.items():
                    # mensa uses (weird) local timestamp
                    timestamp = datetime.fromtimestamp(int(date_unix), pytz.timezone('Europe/Berlin'))

                    day = CanteenDay(canteen_key, day_json, timestamp)
                    days_dict[timestamp.strftime('%d.%m.%Y')] = day
                tmp_canteen_data[canteen_key] = days_dict
            else:
                # no valid data
                tmp_canteen_data[canteen_key] = None

        self._data = tmp_canteen_data

    def get_canteen(self, canteen_key) -> Dict:
        # returns dict containing day objects of the specified canteen
        return self._data[canteen_key]

    def contains_timestamp(self, timestamp: datetime):
        timestamp_str = timestamp.strftime('%d.%m.%Y')

        for canteen_data in self._data.values():
            print(canteen_data)
            if timestamp_str in canteen_data.keys():
                return True

        return False
