from enum import Enum


class CallbackType(Enum):
    selected_date = 'selected_date'
    updated_canteen = 'updated_canteen'
    selected_set_canteen = 'selected_set_canteen'
    selected_show_menu = 'show_menu'
    selected_show_start = 'selected_show_start'
    selected_configuration = 'selected_configuration'
    updated_price_group = 'updated_price_group'
    selected_set_price_group = 'selected_set_price_group'
    selected_toggle_notifications = 'selected_toggle_notifications'
