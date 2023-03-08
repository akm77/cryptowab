from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message


class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config, db_session, http_session) -> None:
        self.config = config
        self.db_session = db_session
        self.http_session = http_session

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        data["config"] = self.config
        data["db_session"] = self.db_session
        data["http_session"] = self.http_session
        return await handler(event, data)
