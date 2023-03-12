import operator

from aiogram_dialog.widgets.kbd import ScrollingGroup, Select, Row, Button, SwitchTo
from aiogram_dialog.widgets.text import Format

from . import constants, onclick, states


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
