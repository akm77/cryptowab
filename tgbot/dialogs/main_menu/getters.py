import logging

from aiogram.types import Message
from aiogram_dialog import DialogManager

from tgbot.models.dm_implementation import get_address_book_entries, get_address_book_entry_from_db, update_account
from tgbot.utils.decimals import value_to_decimal, format_decimal
from tgbot.utils.net_accounts import get_tron_account_from_net, get_bep20_account_from_net, get_erc20_account_from_net

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
    http_session = middleware_data.get("http_session")

    ctx = dialog_manager.current_context()
    event = dialog_manager.event if isinstance(dialog_manager.event, Message) else dialog_manager.event.message
    started_by = dialog_manager.start_data.get("started_by") or "UNKNOWN"
    address_book_id = event.chat.id
    account_address = ctx.dialog_data.get("account_address")
    account_type = ctx.dialog_data.get("account_type")
    config = middleware_data.get("config")
    api_keys = {'TRC20': config.tron_api_keys,
                'BEP20': config.bsc_scan_api_keys,
                'ERC20': config.etherscan_api_keys}
    match account_type:
        case "TRC20":
            account = await get_tron_account_from_net(http_session=http_session,
                                                      address=account_address, tron_api_keys=api_keys.get("TRC20"))
        case "BEP20":
            account = await get_bep20_account_from_net(http_session=http_session,
                                                       address=account_address, bep20_api_keys=api_keys.get("BEP20"))
        case "ERC20":
            account = await get_erc20_account_from_net(http_session=http_session,
                                                       address=account_address, erc20_api_keys=api_keys.get("ERC20"))
        case _:
            account = None
    if account:
        await update_account(session=session,
                             address=account.address,
                             account_type_id=account.account_type_id,
                             values={"native_balance": account.native_balance,
                                     "token_balance": account.token_balance})

    entry = await get_address_book_entry_from_db(session=session,
                                                 address_book_id=address_book_id,
                                                 account_address=account_address,
                                                 account_type_id=account_type)
    ctx.dialog_data.update(account_type_unit=entry.account.account_type.unit)
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
            "token_threshold": format_decimal(value_to_decimal(
                entry.token_threshold / entry.account.account_type.unit), pre=6),
            "track_native": "✓" if entry.track_native else "☐",
            "native_threshold": format_decimal(value_to_decimal(
                entry.native_threshold / entry.account.account_type.unit), pre=6),
            "schedule": entry.schedule}
