import logging

from aiogram.types import Message
from aiogram_dialog import DialogManager

from tgbot.models.dm_implementation import get_address_book_entries
from tgbot.utils.decimals import value_to_decimal, format_decimal

logger = logging.getLogger(__name__)


async def get_address_book(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('db_session')
    ctx = dialog_manager.current_context()
    event = dialog_manager.event if isinstance(dialog_manager.event, Message) else dialog_manager.event.message
    address_book_entries = await get_address_book_entries(session=session,
                                                          address_book_id=event.chat.id)
    items = [(f"{entry.account_alias} "
              f"{format_decimal(value_to_decimal(entry.account.token_balance/entry.account.account_type.unit), pre=2)} "
              f"{format_decimal(value_to_decimal(entry.account.native_balance/entry.account.account_type.unit), pre=2)}",
              f"{entry.account_address}_{entry.account_type_id}")
             for entry in address_book_entries if address_book_entries]

    return {"items": items}
