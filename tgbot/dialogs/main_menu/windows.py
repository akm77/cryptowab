from aiogram.enums import ContentType
from aiogram_dialog import Window
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const

from . import keyboards, states, onclick, constants, getters, events


def main_menu_window():
    return Window(
        Const("Accounts"),
        keyboards.wallets_list_kbd(on_click=onclick.on_select_wallet),
        Row(Cancel(Const("<<")),
            SwitchTo(Const("+"),
                     id=constants.MainMenu.NEW_WALLET,
                     state=states.MainMenuStates.enter_wallet_address)),
        state=states.MainMenuStates.select_wallet,
        getter=getters.get_address_book
    )


def enter_wallet_address_window():
    return Window(
        Const("👇 Enter account address 👇"),
        MessageInput(events.account_address_handler,
                     content_types=[ContentType.TEXT]),
        state=states.MainMenuStates.enter_wallet_address
    )


def enter_wallet_alias_window():
    pass
