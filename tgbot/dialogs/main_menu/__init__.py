from aiogram_dialog import Dialog

from ..main_menu import windows


def main_menu_dialogs():
    return [
        Dialog(
            windows.main_menu_window(),
            windows.enter_wallet_address_window(),
            on_start=None,
            on_process_result=None
        )
    ]
