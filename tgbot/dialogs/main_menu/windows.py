from aiogram_dialog import Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const

from . import keyboards, states, onclick, constants, getters, events


def main_menu_window():
    return Window(
        Const("Wallets"),
        keyboards.wallets_list_kbd(on_click=onclick.on_select_wallet),
        Row(Cancel(Const("<<")),
            SwitchTo(Const("+"),
                     id=constants.MainMenu.NEW_WALLET,
                     state=states.MainMenuStates.enter_wallet_address)),
        state=states.MainMenuStates.select_wallet,
        getter=getters.get_wallets
    )


def enter_wallet_address_window():
    return Window(
        Const("👇 Enter wallet address 👇"),
        TextInput(id=constants.MainMenu.ENTER_WALLET_ADDRESS,
                  type_factory=str,
                  on_error=events.on_error_enter_account_address,
                  on_success=events.on_success_enter_account_address),
        state=states.MainMenuStates.enter_wallet_address
    )


def enter_wallet_alias_window():
    pass