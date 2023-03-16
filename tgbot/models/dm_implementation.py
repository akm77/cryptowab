import datetime
import logging
from copy import copy
from sqlite3 import IntegrityError
from typing import Optional, List, Any, Sequence, Generator

from aiogram.types import Message
from aiohttp import ClientSession
from sqlalchemy import update, Result, select, Row, RowMapping, func, Select
from sqlalchemy.dialects.sqlite import insert, Insert
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import joinedload

from tgbot.models.addressbook import AddressBook, Account, AddressBookEntry, AccountStatement, AccountTransaction
from tgbot.utils.net_accounts import get_native_trns_from_net, get_token_trns_from_net
from tgbot.wallet_readers.account_readers import APIAccountTransaction

logger = logging.getLogger(__name__)


def get_upsert_address_book_query(values: List[dict] | dict) -> Insert:
    insert_statement = insert(AddressBook).values(values)
    return insert_statement.on_conflict_do_update(
        index_elements=["id"],
        set_=dict(title=insert_statement.excluded.title,
                  is_active=insert_statement.excluded.is_active,
                  created_at=insert_statement.excluded.created_at,
                  updated_at=insert_statement.excluded.updated_at)).returning(AddressBook)


async def upsert_address_book(session: async_sessionmaker,
                              values: List[dict] | dict) -> Optional[Sequence[AddressBook]]:
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())

    :param values:
    :param session:
    :return:
    """

    statement = get_upsert_address_book_query(values)
    async with session() as session:
        try:
            result: Result = await session.execute(statement, execution_options={"populate_existing": True})
            await session.commit()
            return result.scalars().all()
        except IntegrityError as e:
            logger.error("Error while upserting AddressBook: %r", e)


async def update_address_book_id(session: async_sessionmaker, old_id: int, new_id: int) -> Optional[AddressBook]:
    update_statement = update(AddressBook).where(AddressBook.id == old_id
                                                 ).values(id=new_id
                                                          ).returning(AddressBook)
    async with session() as session:
        result: Result = await session.execute(update_statement)
        await session.commit()
        return result.scalars().one_or_none()


async def read_address_book_by_id(session: async_sessionmaker, id: int) -> Optional[AddressBook]:
    statement = select(AddressBook).options(joinedload(AddressBook.accounts)).where(AddressBook.id == id)
    async with session() as session:
        result: Result = await session.execute(statement)
        return result.scalars().one_or_none()


def get_upsert_account_query(values: List[dict] | dict) -> Insert:
    insert_statement = insert(Account).values(values)
    return insert_statement.on_conflict_do_update(
        index_elements=["address", "account_type_id"],
        set_=dict(native_balance=insert_statement.excluded.native_balance,
                  token_balance=insert_statement.excluded.token_balance,
                  created_at=insert_statement.excluded.created_at,
                  updated_at=insert_statement.excluded.updated_at)).returning(Account)


async def upsert_account(session: async_sessionmaker,
                         values: List[dict] | dict) -> Optional[Sequence[Account]]:
    """
    address: Mapped[str] = mapped_column(String(128), primary_key=True)
    account_type_id: Mapped[str] = mapped_column(String(16), ForeignKey("account_type.id",
                                                                        ondelete="RESTRICT",
                                                                        onupdate="CASCADE"))
    trx_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    token_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    """

    statement = get_upsert_account_query(values)
    async with session() as session:
        try:
            result: Result = await session.execute(statement, execution_options={"populate_existing": True})
            await session.commit()
            return result.scalars().all()
        except IntegrityError as e:
            logger.error("Error while upserting Account: %r", e)


async def compose_address_book_entries(session: async_sessionmaker,
                                       address_book_id: int,
                                       address_book_title: str,
                                       accounts: List[Account]) -> Optional[List[AddressBookEntry]]:
    address_book_values = {"id": address_book_id,
                           "title": address_book_title,
                           "is_active": True}

    accounts_values = [{"address": account.address,
                        "account_type_id": account.account_type_id,
                        "native_balance": account.native_balance,
                        "token_balance": account.token_balance} for account in accounts]

    address_book_entry_values = [{"address_book_id": address_book_id,
                                  "account_address": account.address,
                                  "account_type_id": account.account_type_id,
                                  "account_alias": f"_{address_book_title} "
                                                   f"{account.account_type_id} "
                                                   f"{account.short_address}"} for account in
                                 accounts]

    insert_address_book = get_upsert_address_book_query(address_book_values)
    insert_account = get_upsert_account_query(accounts_values)
    insert_address_book_entries = insert(AddressBookEntry).values(address_book_entry_values).returning(AddressBookEntry)
    async with session() as session:
        try:
            await session.execute(insert_address_book, execution_options={"populate_existing": True})
            await session.execute(insert_account, execution_options={"populate_existing": True})
            result = await session.execute(insert_address_book_entries, execution_options={"populate_existing": True})
            await session.commit()
            return result.scalars().all()
        except Exception as e:
            logger.error("Error while create address book entry %r", e)


async def check_address_book_entry(session: async_sessionmaker,
                                   address_book_id: int,
                                   account_address: str,
                                   account_type_id: str) -> Optional[AddressBookEntry]:
    statement = select(AddressBookEntry).where(
        AddressBookEntry.address_book_id == address_book_id,
        AddressBookEntry.account_address == account_address,
        AddressBookEntry.account_type_id == account_type_id)
    async with session() as session:
        result: Result = await session.execute(statement)
        return result.scalars().one_or_none()


async def ensure_persist_at_db(db_session: async_sessionmaker,
                               accounts: List[Account],
                               message: Message) -> Optional[List[AddressBookEntry]]:
    address_book_id = message.chat.id
    address_book_title = message.from_user.full_name if message.chat.type == "private" else message.chat.title
    return await compose_address_book_entries(session=db_session,
                                              address_book_id=address_book_id,
                                              address_book_title=address_book_title,
                                              accounts=accounts)


async def get_address_book_entries(session: async_sessionmaker,
                                   address_book_id: int) -> Sequence[AddressBookEntry] | None:
    statement = select(AddressBookEntry).where(AddressBookEntry.address_book_id == address_book_id)
    statement = statement.order_by(AddressBookEntry.account_alias)
    statement = statement.options(joinedload(AddressBookEntry.account,
                                             innerjoin=True).joinedload(Account.account_type, innerjoin=True))
    async with session() as session:
        result: Result = await session.execute(statement)
        return result.scalars().all()


async def get_address_book_entry_from_db(session: async_sessionmaker,
                                         address_book_id: int,
                                         account_address: str,
                                         account_type_id: str) -> Optional[AddressBookEntry]:
    statement = select(AddressBookEntry).where(AddressBookEntry.address_book_id == address_book_id,
                                               AddressBookEntry.account_address == account_address,
                                               AddressBookEntry.account_type_id == account_type_id)
    statement = statement.options(joinedload(AddressBookEntry.account,
                                             innerjoin=True).joinedload(Account.account_type, innerjoin=True))
    async with session() as session:
        result: Result = await session.execute(statement)
        return result.scalars().one_or_none()


async def update_address_book_entry(session: async_sessionmaker,
                                    address_book_id: int,
                                    account_address: str,
                                    account_type_id: str,
                                    values: dict) -> Optional[AddressBookEntry]:
    statement = update(AddressBookEntry).where(AddressBookEntry.address_book_id == address_book_id,
                                               AddressBookEntry.account_address == account_address,
                                               AddressBookEntry.account_type_id == account_type_id)
    statement = statement.values(values)
    statement = statement.returning(AddressBookEntry)
    async with session() as session:
        result: Result = await session.execute(statement)
        await session.commit()
        return result.scalars().one_or_none()


async def update_address_book(session: async_sessionmaker,
                              address_book_id: int,
                              values: dict) -> Optional[AddressBook]:
    statement = update(AddressBook).where(AddressBook.id == address_book_id)
    statement = statement.values(values)
    statement = statement.returning(AddressBook)
    async with session() as session:
        result: Result = await session.execute(statement)
        await session.commit()
        return result.scalars().one_or_none()


async def read_account(session: async_sessionmaker, address: str, account_type_id: str) -> Optional[Account]:
    statement = select(Account).where(Account.address == address, Account.account_type_id == account_type_id)
    async with session() as session:
        result: Result = await session.execute(statement)
        return result.scalars().one_or_none()


def get_last_account_statement_query(account_address: str, account_type_id: str) -> Select:
    cte_max_timestamp = select(func.max(AccountStatement.timestamp).label("timestamp"))
    cte_max_timestamp = cte_max_timestamp.where(AccountStatement.account_address == account_address,
                                                AccountStatement.account_type_id == account_type_id)
    cte_max_timestamp = cte_max_timestamp.cte("last_timestamp")
    return select(AccountStatement).where(AccountStatement.account_address == account_address,
                                          AccountStatement.account_type_id == account_type_id,
                                          AccountStatement.timestamp == cte_max_timestamp.c.timestamp)


def get_actual_tx(tx_type: str, account_tx: List[APIAccountTransaction], old_amount: int,
                  account: Account) -> Optional[List[dict] | List]:
    if tx_type not in ("native", "token"):
        return

    op_sum = 0
    values = []
    for tx in account_tx:
        op_sum += tx.amount if tx.to_address == account.address else -tx.amount
        values.append({"tx_type": tx_type,
                       "from_address": tx.from_address,
                       "from_account_type": account.account_type_id,
                       "to_address": tx.to_address,
                       "to_account_type": account.account_type_id,
                       "tx_timestamp": tx.timestamp,
                       "tx_amount": tx.amount})
        if old_amount + op_sum == account.token_balance:
            break
    return values if len(values) else []


async def get_last_account_statement(session: async_sessionmaker,
                                     address: str,
                                     account_type_id: str) -> Optional[AccountStatement]:
    async with session() as session:
        result: Result = await session.execute(
            get_last_account_statement_query(account_address=address,
                                             account_type_id=account_type_id))
    return result.scalars().one_or_none()


def get_account_addresses_from_tx(account_tx: List[APIAccountTransaction],
                                  account: Account) -> Optional[List[dict]]:
    addresses = set()
    for tx in account_tx:
        addresses.add(tx.from_address)
        addresses.add(tx.to_address)
    addresses.remove(account.address)
    return [{"address": address,
             "account_type_id": account.account_type_id} for address in addresses]


async def sync_db_account(session: async_sessionmaker,
                          http_session: ClientSession,
                          account: Account, api_keys: dict) -> Optional[Account]:
    op_timestamp = datetime.datetime.now()
    db_account = await read_account(session=session, address=account.address, account_type_id=account.account_type_id)
    last_account_statement = await get_last_account_statement(session=session,
                                                              address=account.address,
                                                              account_type_id=account.account_type_id)

    update_account_statement_query = None
    if last_account_statement:
        update_account_statement_query = update(AccountStatement
                                                ).where(
            AccountStatement.account_address == last_account_statement.account_address,
            AccountStatement.account_type_id == last_account_statement.account_type_id,
            AccountStatement.timestamp == last_account_statement.timestamp)
        update_account_statement_query = update_account_statement_query.values(
            dict(timestamp=op_timestamp,
                 native_balance=account.native_balance,
                 token_balance=account.token_balance))

    insert_account_statement_query = insert(
        AccountStatement).values(dict(account_address=account.address,
                                      account_type_id=account.account_type_id,
                                      timestamp=op_timestamp,
                                      native_balance=account.native_balance,
                                      token_balance=account.token_balance))

    native_tx = await get_native_trns_from_net(http_session=http_session,
                                               account=account,
                                               api_keys=api_keys) if not db_account or (
            db_account.native_balance != account.native_balance) else None
    token_tx = await get_token_trns_from_net(http_session=http_session,
                                             account=account,
                                             api_keys=api_keys) if not db_account or (
            db_account.token_balance != account.token_balance) else None
    async with session() as session:
        result: Result = await session.execute(get_upsert_account_query(
            dict(address=account.address,
                 account_type_id=account.account_type_id,
                 native_balance=account.native_balance,
                 token_balance=account.token_balance,
                 updated_at=op_timestamp)))
        updated_account: Account = result.scalars().one()
        if last_account_statement:
            upsert_account_statement_query = update_account_statement_query
        else:
            upsert_account_statement_query = insert_account_statement_query
        await session.execute(upsert_account_statement_query)

        for tx_type in ("token", "native"):
            if (tx_type == "token" and not token_tx) or (tx_type == "native" and not native_tx):
                continue
            tx_list = list(token_tx) if tx_type == "token" else list(native_tx)
            actual_tx_values = get_actual_tx(tx_type=tx_type,
                                             account_tx=tx_list,
                                             old_amount=db_account.token_balance if db_account else 0,
                                             account=account)
            account_addresses = get_account_addresses_from_tx(account_tx=tx_list, account=account)
            if len(account_addresses):
                await session.execute(insert(Account).values(account_addresses).on_conflict_do_nothing())
            if len(actual_tx_values):
                insert_statement = insert(AccountTransaction).values(actual_tx_values).on_conflict_do_nothing()
                await session.execute(insert_statement)

        await session.commit()

    return updated_account
