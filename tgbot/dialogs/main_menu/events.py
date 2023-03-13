import logging

from aiogram.types import Message
from aiogram_dialog import DialogManager, ChatEvent
from aiogram_dialog.widgets.common import ManagedWidget
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Checkbox, Counter

from . import states, constants
from ...models.dm_implementation import check_address_book_entry, ensure_persist_at_db, update_address_book_entry, \
    update_address_book
from ...utils.decimals import check_digit_value
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


async def threshold_handler(message: Message, message_input: MessageInput,
                            manager: DialogManager):
    db_session = manager.middleware_data.get("db_session")
    ctx = manager.current_context()
    address_book_id = message.chat.id
    account_address = ctx.dialog_data.get("account_address")
    account_type = ctx.dialog_data.get("account_type")
    account_type_unit = int(ctx.dialog_data.get("account_type_unit"))
    address_book_title = message.from_user.full_name if message.chat.type == "private" else message.chat.title
    values = {}

    match ctx.state:
        case states.MainMenuStates.enter_native_threshold:
            values["native_threshold"] = int(check_digit_value(message.text,
                                                               type_factory=float,
                                                               min=0, max=999) * account_type_unit)
        case states.MainMenuStates.enter_token_threshold:
            values["token_threshold"] = int(check_digit_value(message.text,
                                                              type_factory=float,
                                                              min=0, max=999) * account_type_unit)

    await update_address_book_entry(session=db_session,
                                    address_book_id=address_book_id,
                                    account_address=account_address,
                                    account_type_id=account_type,
                                    values=values)
    await update_address_book(session=db_session,
                              address_book_id=address_book_id,
                              values={"title": address_book_title})
    await manager.switch_to(states.MainMenuStates.edit_ab_entry)


async def on_track_changed(event: ChatEvent, widget: ManagedWidget[Checkbox], manager: DialogManager):
    db_session = manager.middleware_data.get("db_session")
    ctx = manager.current_context()
    event = manager.event if isinstance(manager.event, Message) else manager.event.message
    address_book_id = event.chat.id
    address_book_title = event.from_user.full_name if event.chat.type == "private" else event.chat.title
    account_address = ctx.dialog_data.get("account_address")
    account_type = ctx.dialog_data.get("account_type")
    values = {"track_native": ctx.widget_data.get(constants.MainMenu.TRACK_NATIVE_TOKEN),
              "track_token": ctx.widget_data.get(constants.MainMenu.TRACK_TOKEN)}
    await update_address_book_entry(session=db_session,
                                    address_book_id=address_book_id,
                                    account_address=account_address,
                                    account_type_id=account_type,
                                    values=values)
    await update_address_book(session=db_session,
                              address_book_id=address_book_id,
                              values={"title": address_book_title})


async def schedule_period_handler(message: Message, message_input: MessageInput,
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
                                    values={"schedule": int(check_digit_value(message.text,
                                                                              type_factory=int,
                                                                              min=1, max=59))})
    await update_address_book(session=db_session,
                              address_book_id=address_book_id,
                              values={"title": address_book_title})
    await manager.switch_to(states.MainMenuStates.edit_ab_entry)
