import logging
from typing import Optional, List

from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.api.internal import Widget
from aiogram_dialog.widgets.input import MessageInput
from sqlalchemy.ext.asyncio import async_sessionmaker

from . import states
from ...models.dm_implementation import read_account_by_address, read_address_book_by_id
from ...models.addressbook import Account
from ...wallet_readers.account_readers import TronAccountReader, EthereumAccountReader, BSCSCAN_API_URL, \
    BSCSCAN_USDT_CONTRACT

logger = logging.getLogger(__name__)


async def ensure_account_at_net(http_session, address, api_keys: dict) -> Optional[List[Account]]:
    accounts = []
    tron = TronAccountReader(session=http_session,
                             address=address,
                             api_keys=api_keys.get('TRC20'),
                             logger=logger)

    if balance := await tron.get_account_data():
        accounts.append(Account(address=address, account_type='TRC20', native_balance=balance.native_balance,
                                token_balance=balance.token_balance))

    etherscan = EthereumAccountReader(session=http_session,
                                      address=address,
                                      api_keys=api_keys.get('ERC20'),
                                      logger=logger)
    if balance := await etherscan.get_account_data():
        accounts.append(Account(address=address.lower(), account_type='ERC20', native_balance=balance.native_balance,
                                token_balance=balance.token_balance))

    etherscan.url = BSCSCAN_API_URL
    etherscan.usdt_contract = BSCSCAN_USDT_CONTRACT
    etherscan.api_keys = api_keys.get('BEP20')
    if balance := await etherscan.get_account_data():
        accounts.append(Account(address=address.lower(), account_type='BEP20', native_balance=balance.native_balance,
                                token_balance=balance.token_balance))
    return accounts if len(accounts) else None


async def ensure_persist_at_db(db_session: async_sessionmaker, accounts: List[Account], message: Message):
    pass


async def on_error_enter_account_address(message: Message, widget: Widget, manager: DialogManager):
    await message.answer("Error in account address")
    await manager.switch_to(states.MainMenuStates.select_wallet)


async def account_address_handler(message: Message, message_input: MessageInput,
                                  manager: DialogManager):
    db_session = manager.middleware_data.get("db_session")
    http_session = manager.middleware_data.get("http_session")
    config = manager.middleware_data.get("config")
    api_keys = {'TRC20': config.tron_api_keys,
                'BEP20': config.bsc_scan_api_keys,
                'ERC20': config.etherscan_api_keys}
    accounts = await ensure_account_at_net(http_session, message.text, api_keys)
    if accounts:
        await ensure_persist_at_db(db_session, accounts, message)
    await manager.switch_to(states.MainMenuStates.select_wallet)
