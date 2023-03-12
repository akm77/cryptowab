from aiogram.fsm.state import StatesGroup, State


class MainMenuStates(StatesGroup):
    select_ab_entry = State()
    edit_ab_entry = State()
    enter_account_address = State()
    enter_account_alias = State()
