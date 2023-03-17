from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.api.internal import Widget
from aiogram_dialog.widgets.kbd import Button

from . import states, constants
from ...models.db_commands import delete_entry


async def on_select_entry(callback: CallbackQuery,
                          widget: Widget,
                          manager: DialogManager,
                          data: str):
    ctx = manager.current_context()
    account_address, account_type = data.split("_")
    ctx.dialog_data.update(account_address=account_address, account_type=account_type)
    await manager.switch_to(states.MainMenuStates.edit_ab_entry)


async def on_click_show_trns(callback: CallbackQuery,
                             button: Button,
                             manager: DialogManager):
    db_session = manager.middleware_data.get("db_session")
    http_session = manager.middleware_data.get("http_session")
    ctx = manager.current_context()
    account_address = ctx.dialog_data.get("account_address")
    account_type = ctx.dialog_data.get("account_type")
    message_text = (ctx.dialog_data.get("token_transactions_text")
                    if button.widget_id == constants.MainMenu.SHOW_TOKEN_TRNS_BUTTON
                    else ctx.dialog_data.get("native_transactions_text"))
    if len(message_text):
        await callback.message.answer(message_text)
        await manager.done()
        await manager.start(states.MainMenuStates.select_ab_entry,
                            data={"started_by": callback.message.from_user.mention_html()},
                            mode=StartMode.RESET_STACK)


async def on_click_delete_entry(callback: CallbackQuery,
                                button: Button,
                                manager: DialogManager):
    db_session = manager.middleware_data.get("db_session")
    ctx = manager.current_context()
    address_book_id = callback.message.chat.id
    account_address = ctx.dialog_data.get("account_address")
    account_type = ctx.dialog_data.get("account_type")
    deleted_entry = await delete_entry(session=db_session,
                                       address_book_id=address_book_id,
                                       account_address=account_address,
                                       account_type_id=account_type)
    if deleted_entry:
        message_text = f"Entry {deleted_entry.account_alias} deleted successfully!"
        await callback.message.answer(message_text)
        await manager.switch_to(states.MainMenuStates.select_ab_entry)
    else:
        await callback.message.answer("Entry was not deleted. Try again.")

