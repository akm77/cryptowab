from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from ..dialogs.main_menu import states

user_router = Router()


@user_router.message(CommandStart())
async def user_start(message: Message, dialog_manager: DialogManager, **kwargs):
    await dialog_manager.start(states.MainMenuStates.select_ab_entry,
                               data={"started_by": message.from_user.mention_html()})
