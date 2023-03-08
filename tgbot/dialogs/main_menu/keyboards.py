import operator

from aiogram_dialog.widgets.kbd import ScrollingGroup, Select
from aiogram_dialog.widgets.text import Format

from . import constants


def wallets_list_kbd(on_click, on_page_changed=None):
    return ScrollingGroup(
        Select(
            Format("{item[0]}"),
            id=constants.MainMenu.WALLET_ITEMS,
            item_id_getter=operator.itemgetter(1),
            items="items",
            on_click=on_click,
        ),
        id=constants.MainMenu.WALLET_ITEMS_SCROLLING_GROUP,
        width=1, height=10,
        on_page_changed=on_page_changed,
        hide_on_single_page=True
    )

