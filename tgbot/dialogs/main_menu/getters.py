import logging

from aiogram.types import Message
from aiogram_dialog import DialogManager

from tgbot.models.db_commands import get_address_book_entries, get_address_book_entry_from_db, sync_db_account, \
    read_account
from tgbot.utils.decimals import value_to_decimal, format_decimal
from tgbot.utils.net_accounts import get_tron_account_from_net, get_bep20_account_from_net, get_erc20_account_from_net, \
    get_native_trns_from_net, get_token_trns_from_net

logger = logging.getLogger(__name__)


async def get_address_book(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('db_session')

    started_by = dialog_manager.start_data.get("started_by") or "UNKNOWN"
    event = dialog_manager.event if isinstance(dialog_manager.event, Message) else dialog_manager.event.message
    address_book_entries = await get_address_book_entries(session=session,
                                                          address_book_id=event.chat.id)
    address_book_title = event.from_user.full_name if event.chat.type == "private" else event.chat.title
    items = [(f"{entry.account_alias} | "
              f"{format_decimal(value_to_decimal(entry.account.token_balance / entry.account.account_type.token_unit), pre=2)} | "
              f"{format_decimal(value_to_decimal(entry.account.native_balance / entry.account.account_type.native_unit), pre=2)}",
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
                                                      address=account_address,
                                                      tron_api_keys=api_keys.get("TRC20"))
        case "BEP20":
            account = await get_bep20_account_from_net(http_session=http_session,
                                                       address=account_address, bep20_api_keys=api_keys.get("BEP20"))
        case "ERC20":
            account = await get_erc20_account_from_net(http_session=http_session,
                                                       address=account_address, erc20_api_keys=api_keys.get("ERC20"))
        case _:
            account = None
            native_transactions = None
            token_transactions = None

    if account:
        db_account = await read_account(session=session, address=account.address,
                                        account_type_id=account.account_type_id)
        native_tx = await get_native_trns_from_net(http_session=http_session,
                                                   account=account,
                                                   api_keys=api_keys) if not db_account or (
                db_account.native_balance != account.native_balance) else None
        token_tx = await get_token_trns_from_net(http_session=http_session,
                                                 account=account,
                                                 api_keys=api_keys) if not db_account or (
                db_account.token_balance != account.token_balance) else None
        await sync_db_account(session=session,
                              db_account=db_account,
                              net_account=account,
                              tx={"token": token_tx,
                                  "native": native_tx})

    entry = await get_address_book_entry_from_db(session=session,
                                                 address_book_id=address_book_id,
                                                 account_address=account_address,
                                                 account_type_id=account_type)
    # entry.account.account_type.unit
    native_transactions_text = "native_transactions_text"
    token_transactions_text = "token_transactions_text"
    ctx.dialog_data.update(native_transactions_text=native_transactions_text)
    ctx.dialog_data.update(token_transactions_text=token_transactions_text)
    ctx.dialog_data.update(native_unit=entry.account.account_type.native_unit)
    ctx.dialog_data.update(token_unit=entry.account.account_type.token_unit)

    return {"started_by": started_by,
            "account_alias": entry.account_alias,
            "account_address": entry.account_address,
            "native_token": entry.account.account_type.native_token,
            "native_balance": format_decimal(value_to_decimal(
                entry.account.native_balance / entry.account.account_type.native_unit), pre=2),
            "account_type": entry.account_type_id,
            "token_balance": format_decimal(value_to_decimal(
                entry.account.token_balance / entry.account.account_type.native_unit), pre=2),
            "track_token": "✓" if entry.track_token else "☐",
            "token_threshold": format_decimal(value_to_decimal(
                entry.token_threshold / entry.account.account_type.token_unit), pre=6),
            "track_native": "✓" if entry.track_native else "☐",
            "native_threshold": format_decimal(value_to_decimal(
                entry.native_threshold / entry.account.account_type.native_unit), pre=6),
            "schedule": entry.schedule}
