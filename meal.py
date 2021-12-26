from typing import Dict, List


class Meal:
    KEY_NAME_MEAL = "meal"
    KEY_NAME_DISH = "dish"

    # price groups
    KEY_NAME_PRICE = "price_1"
    KEY_NAME_PRICE2 = "price_2"
    KEY_NAME_PRICE3 = "price_3"
    KEY_NAME_PRICE4 = "price_4"

    PRICE_GROUPS = {
        KEY_NAME_PRICE: "Studenten",
        KEY_NAME_PRICE2: "Gäste",
        KEY_NAME_PRICE3: "Bedienstete",
        KEY_NAME_PRICE4: "Schüler",
    }

    def __init__(self, data: dict) -> None:
        super().__init__()

        self.meal_name: str = data[self.KEY_NAME_MEAL]
        self.dish_description: str = data[self.KEY_NAME_DISH]
        self.price_dict: Dict[str, float] = {
            self.KEY_NAME_PRICE: data[self.KEY_NAME_PRICE],
            self.KEY_NAME_PRICE2: data[self.KEY_NAME_PRICE2],
            self.KEY_NAME_PRICE3: data[self.KEY_NAME_PRICE3],
            self.KEY_NAME_PRICE4: data[self.KEY_NAME_PRICE4],
        }

    def get_price(self, price_group: str = KEY_NAME_PRICE) -> float:
        return self.price_dict[price_group]

    @classmethod
    def get_price_group_keys(cls) -> List:
        return list(cls.PRICE_GROUPS.keys())

    @classmethod
    def get_price_group_names(cls) -> List:
        return list(cls.PRICE_GROUPS.values())

    @classmethod
    def get_price_group_name(cls, key: str) -> List:
        return cls.PRICE_GROUPS[key]

    @classmethod
    def get_price_group(cls, key: str) -> List:
        return cls.PRICE_GROUPS[key]

    def __str__(self) -> str:
        return f'({self.meal_name} - {self.dish_description} ({self.price_dict[self.KEY_NAME_PRICE]}€))'
