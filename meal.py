class Meal:
    KEY_NAME_MEAL = "meal"
    KEY_NAME_DISH = "dish"
    KEY_NAME_PRICE = "price_1"

    def __init__(self, data: dict) -> None:
        super().__init__()

        self.meal_name: str = data[self.KEY_NAME_MEAL]
        self.dish_description: str = data[self.KEY_NAME_DISH]
        self.price: float = data[self.KEY_NAME_PRICE]

    def __str__(self) -> str:
        return f'({self.meal_name} - {self.dish_description} ({self.price}€))'