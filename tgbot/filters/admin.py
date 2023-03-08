from aiogram.filters import BaseFilter
from aiogram.types import Message

from tgbot.config import settings, Settings


class AdminFilter(BaseFilter):
    is_admin: bool = True

    async def __call__(self, obj: Message, config: Settings) -> bool:
        return (obj.from_user.id in config.admins) == self.is_admin
