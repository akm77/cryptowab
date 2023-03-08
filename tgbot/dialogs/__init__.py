from aiogram import Dispatcher
from aiogram_dialog import DialogRegistry

from tgbot.dialogs import main_menu


def setup_dialogs(dp: Dispatcher):
    registry = DialogRegistry()
    for dialog in [
        *main_menu.main_menu_dialogs(),
    ]:
        registry.register(dialog)  # register a dialog

    registry.setup_dp(dp)
