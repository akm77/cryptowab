from aiogram.fsm.state import StatesGroup, State


class MainMenuStates(StatesGroup):
    select_ab_entry = State()
    edit_ab_entry = State()
    enter_account_address = State()
    enter_account_alias = State()
    enter_native_threshold = State()
    enter_token_threshold = State()
    enter_schedule_period = State()
