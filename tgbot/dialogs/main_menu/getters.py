import logging

from aiogram.types import Message
from aiogram_dialog import DialogManager

from tgbot.models.dm_implementation import get_address_book_entries, get_address_book_entry_from_db
from tgbot.utils.decimals import value_to_decimal, format_decimal

logger = logging.getLogger(__name__)


async def get_address_book(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('db_session')
    started_by = dialog_manager.start_data.get("started_by") or "UNKNOWN"
    event = dialog_manager.event if isinstance(dialog_manager.event, Message) else dialog_manager.event.message
    address_book_entries = await get_address_book_entries(session=session,
                                                          address_book_id=event.chat.id)
    address_book_title = event.from_user.full_name if event.chat.type == "private" else event.chat.title
    items = [(f"{entry.account_alias} | "
              f"{format_decimal(value_to_decimal(entry.account.token_balance / entry.account.account_type.unit), pre=2)} | "
              f"{format_decimal(value_to_decimal(entry.account.native_balance / entry.account.account_type.unit), pre=2)}",
              f"{entry.account_address}_{entry.account_type_id}")
             for entry in address_book_entries if address_book_entries]

    return {"address_book_title": address_book_title,
            "started_by": started_by,
            "items": items}


async def get_started_by(dialog_manager: DialogManager, **middleware_data):
    started_by = dialog_manager.start_data.get("started_by") or "UNKNOWN"
    return {"started_by": started_by}


async def get_address_book_entry(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('db_session')
    ctx = dialog_manager.current_context()
    event = dialog_manager.event if isinstance(dialog_manager.event, Message) else dialog_manager.event.message
    started_by = dialog_manager.start_data.get("started_by") or "UNKNOWN"
    address_book_id = event.chat.id
    account_address = ctx.dialog_data.get("account_address")
    account_type = ctx.dialog_data.get("account_type")
    entry = await get_address_book_entry_from_db(session=session,
                                                 address_book_id=address_book_id,
                                                 account_address=account_address,
                                                 account_type_id=account_type)
    return {"started_by": started_by,
            "account_alias": entry.account_alias,
            "account_address": entry.account_address,
            "native_token": entry.account.account_type.native_token,
            "native_balance": format_decimal(value_to_decimal(
                entry.account.native_balance / entry.account.account_type.unit), pre=2),
            "account_type": entry.account_type_id,
            "token_balance": format_decimal(value_to_decimal(
                entry.account.token_balance / entry.account.account_type.unit), pre=2),
            "track_token": "✓" if entry.track_token else "☐",
            "token_threshold": entry.token_threshold,
            "track_native": "✓" if entry.track_native else "☐",
            "native_threshold": entry.native_threshold,
            "schedule": entry.schedule}
