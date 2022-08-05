from datetime import datetime
from typing import Dict, Set

import requests
from telegram.ext import CallbackContext

import callback_keyboards as keyboards
import canteen_properties as props
import keys as keys
from callback_type import CallbackType
from canteenday import CanteenDay
from meal import Meal
from server_data import ServerData


# BOT MESSAGES

def get_start(chat_operation, update, context: CallbackContext):
    all_canteens = ''
    for canteen_short in CanteenDay.get_canteen_names_short():
        all_canteens += f'\n• {canteen_short}'

    keyboard = keyboards.get_callback_keyboard(
        callback_type=[CallbackType.selected_show_menu, CallbackType.selected_configuration],
        data=[None, None],
        action_text=['Speiseplan', 'Konfiguration'],
    )

    chat_operation(
        'Moin Meister! '
        'Ich bin ein Bot, der dir den aktuellen Speiseplan der Mensen in Karlsruhe anzeigen kann. '
        '\n\n🏠 <b>Unterstützte Mensen</b>'
        f'{all_canteens}'
        f'{get_config_str(update, context)}'
        '\n\n🎉 <b>Anderes</b>'
        '\n• /memes hochwertige, zufällige Memes vom KaIT Subreddit',
        parse_mode='HTML', reply_markup=keyboard)


def get_config(chat_operation, update, context: CallbackContext):
    push_active = get_push_activated(update, context)

    keyboard = keyboards.get_callback_keyboard(
        callback_type=[CallbackType.selected_set_canteen,
                       CallbackType.selected_set_price_group,
                       CallbackType.selected_toggle_notifications,
                       CallbackType.selected_show_start],
        data=[None, None, None, None],
        action_text=['Mensa wählen',
                     'Preisgruppe wählen',
                     f'Benachrichtigungen {"deaktivieren" if push_active else "aktivieren"}',
                     '≪ ZURÜCK'],
        one_per_row=True
    )

    chat_operation(get_config_str(update, context), parse_mode='HTML', reply_markup=keyboard)


def get_price_group_selection(chat_operation, context: CallbackContext):
    keyboard = keyboards.get_callback_keyboard(callback_type=CallbackType.updated_price_group,
                                               data=Meal.get_price_group_keys(),
                                               action_text=Meal.get_price_group_names(),
                                               one_per_row=True
                                               )
    current = Meal.get_price_group_name(get_pricegroup(context.chat_data))
    chat_operation(f'Aktuell eingestellte Preisgruppe: <b>{current}</b>\n\n'
                   f'Preisgruppe ändern:', reply_markup=keyboard, parse_mode='HTML')


def set_canteen(context: CallbackContext, chat_operation):
    keyboard = keyboards.get_callback_keyboard(callback_type=CallbackType.updated_canteen,
                                               data=CanteenDay.get_canteen_keys(),
                                               action_text=CanteenDay.get_canteen_names(),
                                               one_per_row=True
                                               )

    current = CanteenDay.get_name_of(get_user_selected_canteen(chat_data=context.chat_data))
    chat_operation(text=f'Aktuell ausgewählt: <b>{current}</b> \n\nMensa ändern:',
                   reply_markup=keyboard, parse_mode='HTML')


def get_canteen_plan(chat_operation, canteen_data: ServerData, chat_data: Dict, selected_timestamp: datetime = None,
                     send_if_canteen_closed=True,
                     previous_text: str = None, previous_keyboard=None, keyboard_update_operation=None,
                     **kwargs) -> bool:
    selected_timestamp_str = (selected_timestamp if selected_timestamp else datetime.now()).strftime('%d.%m.%Y')

    selected_canteen = get_user_selected_canteen(chat_data=chat_data)

    days_dict = canteen_data.get_canteen(selected_canteen)
    if days_dict is not None and selected_timestamp_str in days_dict.keys():
        canteen_day: CanteenDay = days_dict[selected_timestamp_str]

        if not send_if_canteen_closed and canteen_day.get_canteen_closed():
            # don't send the plan if send_if_canteen_closed is False and the canteen is closed
            return False

        out: str = f'Speiseplan der {canteen_day.get_name()} am <b>{selected_timestamp_str}</b>:\n\n'

        for queue in days_dict[selected_timestamp_str].get_list():
            if not queue.closed:
                # queue name
                out += f'<b>{queue.name}</b>\n'

                # meals
                for meal in queue.meals:
                    out += f'•{meal.meal_name}'

                    price = meal.get_price(get_pricegroup(chat_data))
                    if price != 0:
                        out += ': <u>{:,.2f}€</u>'.format(price)

                    if meal.dish_description:
                        out += f' (<i>{meal.dish_description}</i>)'
                    out += '\n'
            else:
                # queue is closed on this day
                out += f'<b>{queue.name}</b> - geschlossen\n'
            out += '\n'
    else:
        out = f'👾 Für den <b> {selected_timestamp_str}</b> gibt es keinen Mensa Plan ' \
              f'({CanteenDay.get_name_of(selected_canteen)}) 👾'

    out = out.strip()

    keyboard = keyboards.get_select_dates_keyboard(
        days=days_dict,
    )

    if previous_text and previous_text == out:
        # don't publish the update because the text is the same
        if keyboard_update_operation and previous_keyboard and previous_keyboard != keyboard.inline_keyboard:
            # update the keyboard only, if it changed and keyboard_update_operation was provided
            keyboard_update_operation(reply_markup=keyboard)
        return False

    chat_operation(text=out, parse_mode='HTML', reply_markup=keyboard, **kwargs)

    return True


# HELPER

def get_config_str(update, context: CallbackContext):
    # settings
    user_canteen = CanteenDay.get_name_of(get_user_selected_canteen(context.chat_data))
    price_group = Meal.get_price_group_name(get_pricegroup(context.chat_data))
    push_active = get_push_activated(update, context)

    return ('\n\n⚙ <b>Konfiguration</b>'
            f'\n• Mensa: <b>{user_canteen}</b>'
            f'\n• Preisgruppe: <b>{price_group}</b>'
            f'\n• Benachrichtigungen: <b>{"aktiviert 🔔" if push_active else "deaktiviert 🔕"}</b>'
            )


def get_user_selected_canteen(chat_data: Dict = None):
    return chat_data.get(keys.CHAT_DATA_KEY_SELECTED_CANTEEN, props.CANTEEN_KEY_ADENAUER)


def get_meme(subreddit: str = None) -> Dict:
    if subreddit is not None:
        resp = requests.get(url=f'https://meme-api.herokuapp.com/gimme/{subreddit}')
    else:
        resp = requests.get(url='https://meme-api.herokuapp.com/gimme')
    return resp.json()


def get_pricegroup(chat_data: Dict) -> str:
    return chat_data.get(keys.CHAT_DATA_KEY_SELECTED_PRICE_GROUP, Meal.KEY_NAME_PRICE)


def get_push_activated(update, context):
    # check if this chat id is in the push register
    return update.message.chat_id in context.bot_data[keys.BOT_DATA_KEY_PUSH_REGISTER]


def toggle_push(update, context):
    register: Set = context.bot_data[keys.BOT_DATA_KEY_PUSH_REGISTER]

    chat_id = update.message.chat_id
    if chat_id not in register:
        register.add(chat_id)
    else:
        register.remove(chat_id)
