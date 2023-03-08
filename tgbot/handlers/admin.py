from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, ShowMode

from ..dialogs.main_menu import states
from tgbot.filters.admin import AdminFilter

admin_router = Router()
admin_router.message.filter(AdminFilter())


@admin_router.message(CommandStart())
async def admin_start(message: Message, dialog_manager: DialogManager, **kwargs):
    await dialog_manager.start(states.MainMenuStates.select_wallet)
