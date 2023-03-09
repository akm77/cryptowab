import logging
from sqlite3 import IntegrityError
from typing import Optional

from sqlalchemy import update, Result, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import joinedload

from tgbot.models.addressbook import AddressBook, Account, AddressBookEntry

logger = logging.getLogger(__name__)


def get_upsert_address_book_statement(values: dict):
    insert_statement = insert(AddressBook).values(values)
    return insert_statement.on_conflict_do_update(
        index_elements=["id"],
        set_=dict(title=insert_statement.excluded.title,
                  is_active=insert_statement.excluded.is_active)).returning(AddressBook.id)


async def upsert_address_book(session: async_sessionmaker, id: int, title: str, is_active: bool = True) -> Optional[int]:
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())

    :param id:
    :param title:
    :param is_active:
    :param session:
    :return:
    """
    values = {"id": id,
              "title": title,
              "is_active": is_active}
    statement = get_upsert_address_book_statement(values)
    async with session() as session:
        try:
            result: Result = await session.execute(statement)
            await session.commit()
            return result.scalar_one_or_none()
        except IntegrityError as e:
            logger.error("Error while upserting AddressBook: %r", e)


async def update_address_book_id(session: async_sessionmaker, old_id: int, new_id: int) -> Optional[int]:
    update_statement = update(AddressBook).where(AddressBook.id == old_id
                                                 ).values(id=new_id
                                                          ).returning(AddressBook.id)
    async with session() as session:
        result: Result = await session.execute(update_statement)
        await session.commit()
        return result.scalar_one_or_none()


async def read_address_book_by_id(session: async_sessionmaker, id: int) -> Optional[AddressBook]:
    statement = select(AddressBook).options(joinedload(AddressBook.accounts)).where(AddressBook.id == id)
    async with session() as session:
        result: Result = await session.execute(statement)
        return result.scalar_one_or_none()


async def read_account_by_address(session: async_sessionmaker, address: str) -> Optional[Account]:
    statement = select(Account).options(joinedload(Account.account_type)).where(Account.address == address)
    async with session() as session:
        result: Result = await session.execute(statement)
        return result.scalar_one_or_none()


def get_upsert_account_statement(values: dict):
    insert_statement = insert(Account).values(values)
    return insert_statement.on_conflict_do_update(
        index_elements=["address"],
        set_=dict(title=insert_statement.excluded.account_type_id,
                  trx_balance=insert_statement.excluded.native_balance,
                  token_balance=insert_statement.excluded.token_balance)).returning(Account.address)


async def upsert_account(session: async_sessionmaker, address: str, account_type_id: str, native_balance: int,
                         token_balance: int) -> Optional[str]:
    """
    address: Mapped[str] = mapped_column(String(128), primary_key=True)
    account_type_id: Mapped[str] = mapped_column(String(16), ForeignKey("account_type.id",
                                                                        ondelete="RESTRICT",
                                                                        onupdate="CASCADE"))
    trx_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    token_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    """
    values = {"address": address,
              "account_type_id": account_type_id,
              "native_balance": native_balance,
              "token_balance": token_balance}
    statement = get_upsert_account_statement(values)
    async with session() as session:
        try:
            result: Result = await session.execute(statement)
            await session.commit()
            return result.scalar_one_or_none()
        except IntegrityError as e:
            logger.error("Error while upserting Account: %r", e)
