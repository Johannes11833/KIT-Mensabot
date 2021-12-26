from enum import Enum


class CallbackType(Enum):
    selected_date = 'selected_date'
    selected_canteen = 'selected_canteen'
    reselect_canteen = 'select_another_canteen'
    selected_show_menu = 'show_menu'
    selected_set_price_group = 'selected_set_price_group'
