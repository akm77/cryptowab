from aiogram_dialog import Dialog

from ..main_menu import windows


def main_menu_dialogs():
    return [
        Dialog(
            windows.main_menu_window(),
            windows.enter_account_address_window(),
            windows.address_book_entry_window(),
            windows.enter_account_alias_window(),
            on_start=None,
            on_process_result=None
        )
    ]
