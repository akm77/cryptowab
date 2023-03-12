from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.api.internal import Widget

from . import states


async def on_select_entry(callback: CallbackQuery,
                          widget: Widget,
                          manager: DialogManager,
                          data: str):
    ctx = manager.current_context()
    account_address, account_type = data.split("_")
    ctx.dialog_data.update(account_address=account_address, account_type=account_type)
    await manager.switch_to(states.MainMenuStates.edit_ab_entry)


async def on_click_show_trns(callback: CallbackQuery,
                             widget: Widget,
                             manager: DialogManager):
    pass
