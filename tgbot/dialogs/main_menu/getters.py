import logging

from aiogram_dialog import DialogManager

logger = logging.getLogger(__name__)


async def get_wallets(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('db_session')
    ctx = dialog_manager.current_context()
    items = [
        (f"Wallet {i}", i) for i in range(1, 21)
    ]
    return {"items": items}