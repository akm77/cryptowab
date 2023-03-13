from aiogram.enums import ContentType
from aiogram_dialog import Window
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Cancel, Row, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from . import keyboards, states, onclick, constants, getters, events


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


def enter_value_window(text: str, handler=None, state=None, getter=None):
    return Window(
        Format(text),
        MessageInput(handler,
                     content_types=[ContentType.TEXT]),
        state=state,
        getter=getter
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
               "Threshold: {token_threshold} {account_type}\n"
               "====================\n"
               "Track {native_token}: {track_native}\n"
               "Threshold: {native_threshold} {native_token}\n"
               "====================\n"
               "Schedule: one time in {schedule} minute(s)"),
        keyboards.select_transactions_kbd(on_click=onclick.on_click_show_trns),
        keyboards.edit_account_alias_kbd(),
        keyboards.edit_entry_track_options_kbd(),
        keyboards.set_schedule_period_kbd(),
        SwitchTo(Const("<<"),
                 id=constants.MainMenu.BACK_TO_ACCOUNTS,
                 state=states.MainMenuStates.select_ab_entry),
        state=states.MainMenuStates.edit_ab_entry,
        getter=getters.get_address_book_entry
    )
