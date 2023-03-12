from aiogram.enums import ContentType
from aiogram_dialog import Window
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from . import keyboards, states, onclick, constants, getters, events
from .keyboards import select_transactions_kbd, edit_account_alias_kbd


def main_menu_window():
    return Window(
        Format("Accounts in {address_book_title} (started by {started_by})"),
        keyboards.address_book_kbd(on_click=onclick.on_select_entry),
        Row(Cancel(Const("<<")),
            SwitchTo(Const("+"),
                     id=constants.MainMenu.NEW_ACCOUNT,
                     state=states.MainMenuStates.enter_account_address)),
        state=states.MainMenuStates.select_ab_entry,
        getter=getters.get_address_book
    )


def enter_account_address_window():
    return Window(
        Format("Dialog started by {started_by}\n"
               "👇 Enter account address 👇"),
        MessageInput(events.account_address_handler,
                     content_types=[ContentType.TEXT]),
        state=states.MainMenuStates.enter_account_address,
        getter=getters.get_started_by
    )


def enter_account_alias_window():
    return Window(
        Format("Dialog started by {started_by}\n"
               "👇 Enter account alias (Short human readable name) 👇"),
        MessageInput(events.account_alias_handler,
                     content_types=[ContentType.TEXT]),
        state=states.MainMenuStates.enter_account_alias,
        getter=getters.get_started_by
    )


def address_book_entry_window():
    return Window(
        Format("Dialog started by {started_by}\n"
               "--------------------\n"
               "Account alias: {account_alias}\n"
               "Address: {account_address}\n"
               "{native_token}: {native_balance}\n"
               "{account_type}: {token_balance}\n"
               "====================\n"
               "Track {account_type}: {track_token}\n"
               "Threshold: {token_threshold}\n"
               "====================\n"
               "Track {native_token}: {track_native}\n"
               "Threshold: {native_threshold}\n"
               "====================\n"
               "Schedule: one time in {schedule} minute(s)"),
        select_transactions_kbd(on_click=onclick.on_click_show_trns),
        edit_account_alias_kbd(),
        SwitchTo(Const("<<"),
                 id=constants.MainMenu.BACK_TO_ACCOUNTS,
                 state=states.MainMenuStates.select_ab_entry),
        state=states.MainMenuStates.edit_ab_entry,
        getter=getters.get_address_book_entry
    )
