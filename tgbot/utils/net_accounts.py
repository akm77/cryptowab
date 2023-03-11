import logging
from typing import Optional, List

from tgbot.models.addressbook import Account
from tgbot.wallet_readers.account_readers import TronAccountReader, EthereumAccountReader, BSCSCAN_API_URL, \
    BSCSCAN_USDT_CONTRACT

logger = logging.getLogger(__name__)


async def get_tron_account_from_net(http_session, address, tron_api_keys: list) -> Optional[Account]:
    tron = TronAccountReader(session=http_session,
                             address=address,
                             api_keys=tron_api_keys,
                             logger=logger)

    if account := await tron.get_account_data():
        return Account(address=address, account_type='TRC20',
                       native_balance=account.native_balance,
                       token_balance=account.token_balance)


async def get_erc20_account_from_net(http_session, address, erc20_api_keys: list) -> Optional[Account]:
    etherscan = EthereumAccountReader(session=http_session,
                                      address=address,
                                      api_keys=erc20_api_keys,
                                      logger=logger)
    if account := await etherscan.get_account_data():
        return Account(address=address.lower(),
                       account_type='ERC20',
                       native_balance=account.native_balance,
                       token_balance=account.token_balance)


async def get_bep20_account_from_net(http_session, address, bep20_api_keys: list) -> Optional[Account]:
    bscscan = EthereumAccountReader(session=http_session,
                                    url=BSCSCAN_API_URL,
                                    usdt_contract=BSCSCAN_USDT_CONTRACT,
                                    address=address,
                                    api_keys=bep20_api_keys,
                                    logger=logger)
    if account := await bscscan.get_account_data():
        return Account(address=address.lower(),
                       account_type='BEP20',
                       native_balance=account.native_balance,
                       token_balance=account.token_balance)


async def ensure_account_at_net(http_session, address, api_keys: dict) -> Optional[List[Account]]:
    accounts = []

    if account := await get_tron_account_from_net(http_session, address, api_keys.get('TRC20')):
        accounts.append(Account(address=address, account_type='TRC20', native_balance=account.native_balance,
                                token_balance=account.token_balance))
        return accounts

    if account := await get_erc20_account_from_net(http_session, address, api_keys.get('ERC20')):
        accounts.append(Account(address=address.lower(), account_type='ERC20', native_balance=account.native_balance,
                                token_balance=account.token_balance))

    if account := await get_bep20_account_from_net(http_session, address, api_keys.get('BEP20')):
        accounts.append(Account(address=address.lower(), account_type='BEP20', native_balance=account.native_balance,
                                token_balance=account.token_balance))

    return accounts if len(accounts) else None
