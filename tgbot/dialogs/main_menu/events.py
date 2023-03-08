import logging
from typing import Optional, List

from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.api.internal import Widget

from . import states
from ...models.dm_implementation import read_account_by_address, read_address_book_by_id, upsert_account, \
    upsert_address_book
from ...models.tokenaccount import Account
from ...wallet_readers.url_reader import TronAccountReader, EthereumAccountReader, BSCSCAN_API_URL, \
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
        accounts.append(Account(address=address, account_type='ERC20', native_balance=balance.native_balance,
                                token_balance=balance.token_balance))

    bscscan = EthereumAccountReader(session=http_session,
                                    address=address,
                                    api_keys=api_keys.get('BEP20'),
                                    url=BSCSCAN_API_URL,
                                    usdt_contract=BSCSCAN_USDT_CONTRACT,
                                    logger=logger)
    if balance := await bscscan.get_account_data():
        accounts.append(Account(address=address, account_type='BEP20', native_balance=balance.native_balance,
                                token_balance=balance.token_balance))
    return accounts if len(accounts) else None


async def on_error_enter_account_address(message: Message, widget: Widget, manager: DialogManager):
    await message.answer("Error in wallet address")
    await manager.switch_to(states.MainMenuStates.select_wallet)


async def on_success_enter_account_address(message: Message, widget: Widget, manager: DialogManager, address):
    db_session = manager.middleware_data.get("db_session")
    http_session = manager.middleware_data.get("http_session")
    config = manager.middleware_data.get("config")
    api_keys = {'TRC20': config.tron_api_keys,
                'BEP20': config.bsc_scan_api_keys,
                'ERC20': config.etherscan_api_keys}
    accounts = await ensure_account_at_net(http_session, address, api_keys)
    db_account = await read_account_by_address(db_session, address)
    address_book = await read_address_book_by_id(session=db_session, id=message.chat.id)
    if accounts:
        m = [(f"Wallet address {net_account.address} added successfully\n"
              f"TOKEN: {net_account.native_balance}\n{net_account.account_type_id} {net_account.token_balance}\n")
             for net_account in accounts]

        message_text = "\n".join(m)
    else:
        message_text = f"Wrong wallet address {address}"
    await message.answer(message_text)
    await manager.switch_to(states.MainMenuStates.select_wallet)
