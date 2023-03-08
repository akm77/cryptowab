from aiogram.fsm.state import StatesGroup, State


class MainMenuStates(StatesGroup):
    select_wallet = State()
    edit_wallet = State()
    enter_wallet_address = State()
