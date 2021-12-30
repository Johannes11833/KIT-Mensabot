from typing import Dict, List

from meal import Meal


class Queue:
    name: str
    KEY_NAME_NO_DATA = "nodata"

    def __init__(self, name: str, queue_json: Dict) -> None:
        super().__init__()
        self.name = name
        self.meals: List[Meal] = []

        self.closed = queue_json is None or self.KEY_NAME_NO_DATA in queue_json[0].keys()

        if not self.closed:
            for meal_json in queue_json:
                self.meals.append(Meal(meal_json))
