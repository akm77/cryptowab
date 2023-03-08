from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.api.internal import Widget


async def on_select_wallet(callback: CallbackQuery,
                           widget: Widget,
                           manager: DialogManager,
                           data: str):
    pass
    ctx = manager.current_context()
