import logging

from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput

from . import states
from ...models.dm_implementation import check_address_book_entry, ensure_persist_at_db, update_address_book_entry, \
    update_address_book
from ...utils.net_accounts import ensure_account_at_net

logger = logging.getLogger(__name__)


async def account_address_handler(message: Message, message_input: MessageInput,
                                  manager: DialogManager):
    db_session = manager.middleware_data.get("db_session")
    http_session = manager.middleware_data.get("http_session")
    config = manager.middleware_data.get("config")
    api_keys = {'TRC20': config.tron_api_keys,
                'BEP20': config.bsc_scan_api_keys,
                'ERC20': config.etherscan_api_keys}
    accounts = await ensure_account_at_net(http_session, message.text, api_keys)
    if not accounts:
        message_text = f"Wrong account address {message.text}"
        await message.answer(message_text)
        await manager.switch_to(states.MainMenuStates.select_ab_entry)
        return

    address_book_id = message.chat.id

    message_text = ""
    for account in accounts:
        entry = await check_address_book_entry(session=db_session,
                                               address_book_id=address_book_id,
                                               account_address=account.address,
                                               account_type_id=account.account_type_id)
        if entry:
            message_text += f"{entry.account_alias} ({entry.account_address}) already in address book.\n"
            continue
        address_book_entries = await ensure_persist_at_db(db_session, [account], message)
        if address_book_entries:
            message_text += f"Account {address_book_entries[0].account_alias} was added\n"

    await message.answer(message_text)
    await manager.switch_to(states.MainMenuStates.select_ab_entry)


async def account_alias_handler(message: Message, message_input: MessageInput,
                                manager: DialogManager):
    db_session = manager.middleware_data.get("db_session")
    ctx = manager.current_context()
    address_book_id = message.chat.id
    account_address = ctx.dialog_data.get("account_address")
    account_type = ctx.dialog_data.get("account_type")
    address_book_title = message.from_user.full_name if message.chat.type == "private" else message.chat.title
    await update_address_book_entry(session=db_session,
                                    address_book_id=address_book_id,
                                    account_address=account_address,
                                    account_type_id=account_type,
                                    values={"account_alias": message.text})
    await update_address_book(session=db_session,
                              address_book_id=address_book_id,
                              values={"title": address_book_title})
    await manager.switch_to(states.MainMenuStates.edit_ab_entry)
