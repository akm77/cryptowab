from datetime import datetime
from typing import List

from sqlalchemy import text, Boolean, String, ForeignKey, CheckConstraint, ForeignKeyConstraint, DateTime, \
    UniqueConstraint
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
    native_unit: Mapped[int] = mapped_column(VeryBigInt, server_default=text("1000000"))
    token_unit: Mapped[int] = mapped_column(VeryBigInt, server_default=text("1000000"))
    token_contract: Mapped[str] = mapped_column(String(128), nullable=False)

    def __repr__(self) -> str:
        return f"AccountType(id={self.id!r}, unit={self.native_unit!r})"


class Account(TimestampMixin, Base):
    __tablename__ = "account"

    address: Mapped[str] = mapped_column(String(128), primary_key=True)
    account_type_id: Mapped[str] = mapped_column(String(16), ForeignKey("account_type.id",
                                                                        ondelete="RESTRICT",
                                                                        onupdate="CASCADE"),
                                                 primary_key=True)
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
        return (f"Account(id={self.address!r}, account type={self.account_type_id!r}, "
                f"native balance={self.native_balance!r}), token balance={self.token_balance!r}")


class AccountStatement(Base):
    __tablename__ = "account_statement"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_address", "account_type_id"], ["account.address", "account.account_type_id"],
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
    )

    account_address: Mapped[str] = mapped_column(String(128), nullable=False, primary_key=True)
    account_type_id: Mapped[str] = mapped_column(String(16), nullable=False, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(True), nullable=False, primary_key=True)
    native_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    token_balance: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))
    account: Mapped["Account"] = relationship()

    def __repr__(self) -> str:
        return (f"Account(id={self.account_address!r}, "
                f"account type={self.account_type_id!r}, "
                f"timestamp={self.timestamp!r}"
                f"native balance={self.native_balance!r}), "
                f"token balance={self.token_balance!r}")


class AccountTransaction(Base):
    __tablename__ = "account_tx"
    __table_args__ = (
        ForeignKeyConstraint(
            ["from_address", "from_account_type"], ["account.address", "account.account_type_id"],
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        ForeignKeyConstraint(
            ["to_address", "to_account_type"], ["account.address", "account.account_type_id"],
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
    )
    tx_type: Mapped[str] = mapped_column(String(10),
                                         CheckConstraint("tx_type IN ('native', 'token')",
                                                         name="check_tx_type"),
                                         nullable=False, primary_key=True)
    from_address: Mapped[str] = mapped_column(String(128), nullable=False, primary_key=True)
    from_account_type: Mapped[str] = mapped_column(String(16), nullable=False, primary_key=True)
    to_address: Mapped[str] = mapped_column(String(128), nullable=False, primary_key=True)
    to_account_type: Mapped[str] = mapped_column(String(16), nullable=False, primary_key=True)
    tx_timestamp: Mapped[datetime] = mapped_column(DateTime(True), nullable=False, primary_key=True)
    tx_amount: Mapped[int] = mapped_column(VeryBigInt, server_default=text("0"))

    from_account: Mapped["Account"] = relationship(foreign_keys=[from_address, from_account_type])
    to_account: Mapped["Account"] = relationship(foreign_keys=[to_address, to_account_type])

    def __init__(self, tx_type, account_type, from_address, to_address, tx_timestamp, tx_amount):
        super().__init__()
        self.tx_type = tx_type
        self.from_address = from_address
        self.from_account_type = account_type
        self.to_address = to_address
        self.to_account_type = account_type
        self.tx_timestamp = tx_timestamp
        self.tx_amount = tx_amount

    def __repr__(self) -> str:
        return (f"Tx type(tx_type={self.tx_type!r}, "
                f"account type={self.from_account_type!r}, "
                f"from address={self.from_address!r}), "
                f"to address={self.to_address!r}, "
                f"timestamp={self.tx_timestamp!r}, "
                f"amount={self.tx_amount!r}")


class AddressBook(TimestampMixin, Base):
    __tablename__ = "address_book"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    accounts: Mapped[List["AddressBookEntry"]] = relationship()

    def __repr__(self) -> str:
        return f"AddressBook(id={self.id!r}, title={self.title!r}, is_active={self.is_active!r}"


class AddressBookEntry(Base):
    __tablename__ = "address_book_entry"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_address", "account_type_id"], ["account.address", "account.account_type_id"],
            ondelete="RESTRICT",
            onupdate="CASCADE"
        ),
        UniqueConstraint("address_book_id", "account_address", "account_alias",
                         name="uq_address_book_entry_address_book_id_account_address_account_alias")
    )
    address_book_id: Mapped[int] = mapped_column(ForeignKey("address_book.id",
                                                            ondelete="CASCADE",
                                                            onupdate="CASCADE"),
                                                 nullable=False,
                                                 primary_key=True)
    account_address: Mapped[str] = mapped_column(String(128), nullable=False, primary_key=True)
    account_type_id: Mapped[str] = mapped_column(String(16), nullable=False, primary_key=True)

    account_alias: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    track_native: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.false())
    native_threshold: Mapped[int] = mapped_column(nullable=False, server_default=text("10"))
    track_token: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=expression.false())
    token_threshold: Mapped[int] = mapped_column(nullable=False, server_default=text("10"))
    schedule: Mapped[int] = mapped_column(nullable=False, server_default=text("10"))

    account: Mapped["Account"] = relationship()

    @property
    def short_address(self):
        return self.account_address[:3] + "..." + self.account_address[-3:]

    def __repr__(self) -> str:
        return (f"AddressBookEntry(address_book_id={self.address_book_id!r}, "
                f"account_address={self.account_address!r}, account type {self.account_type_id!r}"
                f"account_alias={self.account_alias!r}), track_native={self.track_native!r}, "
                f"track_token={self.track_token!r}, schedule={self.schedule!r}")
