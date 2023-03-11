from asyncio import sleep
from math import inf

from aiogram import Router, types, F, html, Bot
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from cachetools import TTLCache

from tgbot.models.dm_implementation import update_address_book_id, read_address_book_by_id, upsert_address_book
from tgbot.services import broadcaster

"""
This is a simple TTL Cache, so that my_chat_member doesn't trigger on group to supergroup migration event
"""
cache = TTLCache(maxsize=inf, ttl=10.0)

bot_chat_member_router = Router()


@bot_chat_member_router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=JOIN_TRANSITION
    )
)
async def on_bot_join(event: types.ChatMemberUpdated, bot: Bot, **middleware_data):
    """
    Bot was added to group.
    :param event: an event from Telegram of type "my_chat_member"
    :param bot: bot who message was addressed to
    :return:
    """
    await sleep(1.0)
    if event.chat.id not in cache.keys():
        chat_title = event.chat.title or event.from_user.full_name
        config = middleware_data.get("config")
        session = middleware_data.get("db_session")
        address_book = await read_address_book_by_id(session=session, id=event.chat.id)

        if address_book and not address_book.is_active:
            await upsert_address_book(session, dict(id=event.chat.id,
                                                    title=chat_title,
                                                    is_active=not address_book.is_active))
        message_text = f"Bot was added to {event.chat.type} chat, chat title is {chat_title}"
        await bot.send_message(
            chat_id=event.chat.id,
            text=message_text
        )

        await sleep(0.5)
        await broadcaster.broadcast(bot, config.admins, message_text)


@bot_chat_member_router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=LEAVE_TRANSITION
    )
)
async def on_bot_leave(event: types.ChatMemberUpdated, bot: Bot, **middleware_data):
    """
    Bot left the group.
    :param event: an event from Telegram of type "my_chat_member"
    :param bot: bot who message was addressed to
    :return:
    """
    await sleep(1.0)

    if event.chat.id not in cache.keys():
        config = middleware_data.get("config")
        session = middleware_data.get("db_session")
        address_book = await read_address_book_by_id(session=session, id=event.chat.id)
        chat_title = address_book.title if address_book else event.chat.title
        if address_book and address_book.is_active:
            await upsert_address_book(session, dict(id=event.chat.id,
                                                    title=chat_title,
                                                    is_active=not address_book.is_active))
        message_text = f"Bot was kicked in {event.chat.type} chat, chat title is {chat_title}"
        await broadcaster.broadcast(bot, config.admins, message_text)


@bot_chat_member_router.message(F.migrate_to_chat_id)
async def group_to_supegroup_migration(message: types.Message, bot: Bot, **middleware_data):
    config = middleware_data.get("config")
    session = middleware_data.get("db_session")
    await update_address_book_id(session, message.chat.id, message.migrate_to_chat_id)

    message_text = (f"Group upgraded to supergroup.\n"
                    f"Old ID: {html.code(message.chat.id)}\n"
                    f"New ID: {html.code(message.migrate_to_chat_id)}")

    await bot.send_message(
        message.migrate_to_chat_id,
        message_text
    )

    await sleep(0.5)
    await broadcaster.broadcast(bot, config.admins, message_text)

    cache[message.migrate_to_chat_id] = True
