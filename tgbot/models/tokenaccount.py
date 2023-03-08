from typing import List

from sqlalchemy import text, Boolean, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from .base import Base, VeryBigInt, TimestampMixin


class AccountType(Base):
    __tablename__ = "account_type"

    id: Mapped[str] = mapped_column(String(16),
                                    CheckConstraint("id IN ('BEP20', 'TRC20', 'ERC20')", name="check_id"),
                                    primary_key=True)
    native_token: Mapped[str] = mapped_column(String(16),
                                              CheckConstraint("native_token IN ('BNB', 'TRX', 'ETH')",
                                                              name="check_native_token"))
    unit: Mapped[int] = mapped_column(VeryBigInt, server_default=text("1000000"))
    token_contract: Mapped[str] = mapped_column(String(128), nullable=False)

    def __repr__(self) -> str:
        return f"AccountType(id={self.id!r}, unit={self.unit!r})"


class Account(TimestampMixin, Base):
    __tablename__ = "account"

    address: Mapped[str] = mapped_column(String(128), primary_key=True)
    account_type_id: Mapped[str] = mapped_column(String(16), ForeignKey("account_type.id",
                                                                        ondelete="RESTRICT",
                                                                        onupdate="CASCADE"))
    native_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    token_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    account_type: Mapped["AccountType"] = relationship()

    def __init__(self, address, account_type, native_balance, token_balance):
        super().__init__()
        self.address = address
        self.account_type_id = account_type
        self.native_balance = native_balance
        self.token_balance = token_balance

    @property
    def short_address(self):
        return self.address[:3] + "..." + self.address[-3:]

    def __repr__(self) -> str:
        return (f"Account(id={self.address!r}, account_type={self.account_type_id!r}, "
                f"trx_balance={self.native_balance!r}), token_balance={self.token_balance!r}")


class AddressBook(TimestampMixin, Base):
    __tablename__ = "address_book"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    accounts: Mapped[List["AccountAddressBook"]] = relationship()

    def __repr__(self) -> str:
        return f"AddressBook(id={self.id!r}, title={self.title!r}, is_active={self.is_active!r}"


class AccountAddressBook(Base):
    __tablename__ = "account_address_book"

    address_book_id: Mapped[int] = mapped_column(ForeignKey("address_book.id",
                                                            ondelete="CASCADE",
                                                            onupdate="CASCADE"),
                                                 primary_key=True)
    account_address: Mapped[str] = mapped_column(String(128), ForeignKey("account.address",
                                                                         ondelete="CASCADE",
                                                                         onupdate="CASCADE"),
                                                 primary_key=True)
    account_alias: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    track_trx: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    track_token: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    schedule: Mapped[int] = mapped_column(server_default=text("10"))

    account: Mapped["Account"] = relationship()

    @property
    def short_address(self):
        return self.account_address[:3] + "..." + self.account_address[-3:]

    def __repr__(self) -> str:
        return (f"AccountAddressBook(address_book_id={self.address_book_id!r}, account_id={self.account_address!r}, "
                f"account_alias={self.account_alias!r}), track_trx={self.track_trx!r}, "
                f"track_token={self.track_token!r}, schedule={self.schedule!r}")
