import logging
from typing import Optional, List, Generator, Any

from aiohttp import ClientSession

from tgbot.models.addressbook import Account
from tgbot.wallet_readers.account_readers import TronAccountReader, EthereumAccountReader, BSCSCAN_API_URL, \
    BSCSCAN_USDT_CONTRACT, APIAccountTransaction

logger = logging.getLogger(__name__)


async def get_tron_account_from_net(http_session: ClientSession,
                                    address: str,
                                    tron_api_keys: list) -> Optional[Account]:
    tron = TronAccountReader(session=http_session,
                             address=address,
                             api_keys=tron_api_keys,
                             logger=logger)

    if account := await tron.get_account_data():
        return Account(address=address,
                       account_type='TRC20',
                       native_balance=account.native_balance,
                       token_balance=account.token_balance)


async def get_tron_native_trns_from_net(http_session: ClientSession,
                                        address: str,
                                        tron_api_keys: list) -> Optional[Generator[APIAccountTransaction, Any, None]]:
    tron = TronAccountReader(session=http_session,
                             address=address,
                             api_keys=tron_api_keys,
                             logger=logger)

    return await tron.get_native_transactions()


async def get_tron_token_trns_from_net(http_session: ClientSession,
                                       address: str,
                                       tron_api_keys: list) -> Optional[Generator[APIAccountTransaction, Any, None]]:
    tron = TronAccountReader(session=http_session,
                             address=address,
                             api_keys=tron_api_keys,
                             logger=logger)

    return await tron.get_token_transactions()


async def get_erc20_account_from_net(http_session: ClientSession,
                                     address: str,
                                     erc20_api_keys: list) -> Optional[Account]:
    etherscan = EthereumAccountReader(session=http_session,
                                      address=address,
                                      api_keys=erc20_api_keys,
                                      logger=logger)
    if account := await etherscan.get_account_data():
        return Account(address=address.lower(),
                       account_type='ERC20',
                       native_balance=account.native_balance,
                       token_balance=account.token_balance)


async def get_erc20_native_trns_from_net(http_session: ClientSession,
                                         address: str,
                                         erc20_api_keys: list) -> Optional[Generator[APIAccountTransaction, Any, None]]:
    etherscan = EthereumAccountReader(session=http_session,
                                      address=address,
                                      api_keys=erc20_api_keys,
                                      logger=logger)
    return await etherscan.get_native_transactions()


async def get_erc20_token_trns_from_net(http_session: ClientSession,
                                        address: str,
                                        erc20_api_keys: list) -> Optional[Generator[APIAccountTransaction, Any, None]]:
    etherscan = EthereumAccountReader(session=http_session,
                                      address=address,
                                      api_keys=erc20_api_keys,
                                      logger=logger)
    return await etherscan.get_token_transactions()


async def get_bep20_account_from_net(http_session: ClientSession,
                                     address: str,
                                     bep20_api_keys: list) -> Optional[Account]:
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


async def get_bep20_native_trns_from_net(http_session: ClientSession,
                                         address: str,
                                         bep20_api_keys: list) -> Optional[Generator[APIAccountTransaction, Any, None]]:
    bscscan = EthereumAccountReader(session=http_session,
                                    url=BSCSCAN_API_URL,
                                    usdt_contract=BSCSCAN_USDT_CONTRACT,
                                    address=address,
                                    api_keys=bep20_api_keys,
                                    logger=logger)
    return await bscscan.get_native_transactions()


async def get_bep20_token_trns_from_net(http_session,
                                        address,
                                        bep20_api_keys: list) -> Optional[Generator[APIAccountTransaction, Any, None]]:
    bscscan = EthereumAccountReader(session=http_session,
                                    url=BSCSCAN_API_URL,
                                    usdt_contract=BSCSCAN_USDT_CONTRACT,
                                    address=address,
                                    api_keys=bep20_api_keys,
                                    logger=logger)
    return await bscscan.get_token_transactions()


async def ensure_account_at_net(http_session: ClientSession,
                                address: str,
                                api_keys: dict) -> Optional[List[Account]]:
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


async def get_native_trns_from_net(http_session: ClientSession,
                                   account: Account,
                                   api_keys: dict) -> Generator[APIAccountTransaction, Any, None] | None:
    match account.account_type_id:
        case "TRC20":
            transactions = await get_tron_native_trns_from_net(http_session=http_session,
                                                               address=account.address,
                                                               tron_api_keys=api_keys.get("TRC20"))
        case "BEP20":
            transactions = await get_bep20_native_trns_from_net(http_session=http_session,
                                                                address=account.address,
                                                                bep20_api_keys=api_keys.get("BEP20"))
        case "ERC20":
            transactions = await get_erc20_native_trns_from_net(http_session=http_session,
                                                                address=account.address,
                                                                erc20_api_keys=api_keys.get("ERC20"))
        case _:
            transactions = None
    return transactions


async def get_token_trns_from_net(http_session: ClientSession,
                                  account: Account,
                                  api_keys: dict) -> Generator[APIAccountTransaction, Any, None] | None:
    match account.account_type_id:
        case "TRC20":
            transactions = await get_tron_token_trns_from_net(http_session=http_session,
                                                              address=account.address,
                                                              tron_api_keys=api_keys.get("TRC20"))
        case "BEP20":
            transactions = await get_bep20_token_trns_from_net(http_session=http_session,
                                                               address=account.address,
                                                               bep20_api_keys=api_keys.get("BEP20"))
        case "ERC20":
            transactions = await get_erc20_token_trns_from_net(http_session=http_session,
                                                               address=account.address,
                                                               erc20_api_keys=api_keys.get("ERC20"))
        case _:
            transactions = None
    return transactions
