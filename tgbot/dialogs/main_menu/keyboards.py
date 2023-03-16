import operator

from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Row, Button, SwitchTo, Checkbox, Counter, Group
from aiogram_dialog.widgets.text import Format

from . import constants, states, events, onclick


def address_book_kbd(on_click, on_page_changed=None):
    return ScrollingGroup(
        Select(
            Format("{item[0]}"),
            id=constants.MainMenu.ADDRESS_BOOK,
            item_id_getter=operator.itemgetter(1),
            items="items",
            on_click=on_click,
        ),
        id=constants.MainMenu.ADDRESS_BOOK_SCROLLING_GROUP,
        width=1, height=10,
        on_page_changed=on_page_changed,
        hide_on_single_page=True
    )


def select_transactions_kbd(on_click):
    return Row(
        Button(Format("{account_type} trns"),
               id=constants.MainMenu.SHOW_TOKEN_TRNS_BUTTON,
               on_click=on_click),
        Button(Format("{native_token} trns"),
               id=constants.MainMenu.SHOW_NATIVE_TRNS_BUTTON,
               on_click=on_click)
    )


def edit_account_alias_kbd():
    return Row(
        SwitchTo(Format("Edit alias: {account_alias}"),
                 id=constants.MainMenu.EDIT_ACCOUNT_ALIAS_BUTTON,
                 state=states.MainMenuStates.enter_account_alias)
    )


def delete_entry_kbd():
    return Row(
        Button(Format("❌ Delete {account_alias} ‼️️"),
               id=constants.MainMenu.DELETE_ENTRY_BUTTON,
               on_click=onclick.on_click_delete_entry)
    )


def edit_entry_track_options_kbd():
    return Group(
        Row(
            Checkbox(
                Format("✓  Track {account_type}"),
                Format("Track {account_type}"),
                id=constants.MainMenu.TRACK_TOKEN,
                default=False,  # so it will be checked by default,
                on_state_changed=events.on_track_changed),
            SwitchTo(Format("Threshold: {token_threshold}"),
                     id=constants.MainMenu.TOKEN_THRESHOLD,
                     state=states.MainMenuStates.enter_token_threshold),
            id=constants.MainMenu.TOKEN_OPTIONS
        ),
        Row(
            Checkbox(
                Format("✓  Track {native_token}"),
                Format("Track {native_token}"),
                id=constants.MainMenu.TRACK_NATIVE_TOKEN,
                default=False,  # so it will be checked by default,
                on_state_changed=events.on_track_changed),
            SwitchTo(Format("Threshold: {native_threshold}"),
                     id=constants.MainMenu.NATIVE_TOKEN_THRESHOLD,
                     state=states.MainMenuStates.enter_native_threshold),
            id=constants.MainMenu.NATIVE_TOKEN_OPTIONS
        )
    )


def set_schedule_period_kbd():
    return Row(
        SwitchTo(Format("Schedule: one time in {schedule} minute(s)"),
                 id=constants.MainMenu.SET_SCHEDULE_PERIOD_BUTTON,
                 state=states.MainMenuStates.enter_schedule_period)
    )
