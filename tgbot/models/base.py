import logging
from abc import ABC
from datetime import datetime

from sqlalchemy import event, Engine, MetaData, types, func, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

meta = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})
MAX_SQLITE_INT = 2 ** 63 - 1


class VeryBigInt(types.TypeDecorator, ABC):
    impl = types.Integer
    cache_ok = False

    def process_bind_param(self, value, dialect):
        return hex(value) if value > MAX_SQLITE_INT else value

    def process_result_value(self, value, dialect):
        return int(value, 16) if isinstance(value, str) else value


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=func.datetime('now', 'localtime'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(True), default=func.datetime('now', 'localtime'),
                                                 onupdate=func.datetime('now', 'localtime'),
                                                 server_default=func.datetime('now', 'localtime'))


class Base(DeclarativeBase):
    metadata = meta


async def create_db_session(db_dialect, db_name, db_user, db_pass, db_host, db_echo) -> async_sessionmaker:
    logger = logging.getLogger(__name__)
    # dialect[+driver]: // user: password @ host / dbname[?key = value..],

    if db_dialect.startswith('sqlite'):
        database_uri = f"{db_dialect}:///{db_name}"
    else:
        database_uri = f"{db_dialect}://{db_user}:{db_pass}" \
                       f"@{db_host}/{db_name}"

    engine = create_async_engine(
        database_uri,
        echo=db_echo,
        future=True
    )

    if db_dialect.startswith('sqlite'):
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session = async_sessionmaker(
        engine,
        expire_on_commit=False)
    logger.info(f"Database {database_uri} session successfully configured")
    return session
