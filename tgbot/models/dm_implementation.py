import logging
from sqlite3 import IntegrityError
from typing import Optional, List, Any, Sequence

from aiogram.types import Message
from sqlalchemy import update, Result, select, Row, RowMapping
from sqlalchemy.dialects.sqlite import insert, Insert
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import joinedload

from tgbot.models.addressbook import AddressBook, Account, AddressBookEntry

logger = logging.getLogger(__name__)


def get_upsert_address_book_statement(values: List[dict] | dict) -> Insert:
    insert_statement = insert(AddressBook).values(values)
    return insert_statement.on_conflict_do_update(
        index_elements=["id"],
        set_=dict(title=insert_statement.excluded.title,
                  is_active=insert_statement.excluded.is_active,
                  created_at=insert_statement.excluded.created_at,
                  updated_at=insert_statement.excluded.updated_at)).returning(AddressBook)


async def upsert_address_book(session: async_sessionmaker,
                              values: List[dict] | dict) -> Sequence[Row | RowMapping | Any]:
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())

    :param values:
    :param session:
    :return:
    """

    statement = get_upsert_address_book_statement(values)
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


async def read_account_by_address(session: async_sessionmaker, address: str) -> Optional[Account]:
    statement = select(Account).options(joinedload(Account.account_type)).where(Account.address == address)
    async with session() as session:
        result: Result = await session.execute(statement)
        return result.scalars().one_or_none()


def get_upsert_account_statement(values: List[dict] | dict) -> Insert:
    insert_statement = insert(Account).values(values)
    return insert_statement.on_conflict_do_update(
        index_elements=["address", "account_type_id"],
        set_=dict(native_balance=insert_statement.excluded.native_balance,
                  token_balance=insert_statement.excluded.token_balance,
                  created_at=insert_statement.excluded.created_at,
                  updated_at=insert_statement.excluded.updated_at)).returning(Account)


async def upsert_account(session: async_sessionmaker, values: List[dict] | dict) -> Optional[str]:
    """
    address: Mapped[str] = mapped_column(String(128), primary_key=True)
    account_type_id: Mapped[str] = mapped_column(String(16), ForeignKey("account_type.id",
                                                                        ondelete="RESTRICT",
                                                                        onupdate="CASCADE"))
    trx_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    token_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    """

    statement = get_upsert_account_statement(values)
    async with session() as session:
        try:
            result: Result = await session.execute(statement, execution_options={"populate_existing": True})
            await session.commit()
            return result.scalar_one_or_none()
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
                                  "account_alias": f"{address_book_title} "
                                                   f"{account.account_type_id} "
                                                   f"{account.short_address}"} for account in
                                 accounts]

    insert_address_book = get_upsert_address_book_statement(address_book_values)
    insert_account = get_upsert_account_statement(accounts_values)
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
