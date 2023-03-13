from aiogram_dialog import Dialog

from ..main_menu import windows, events, states, getters


def main_menu_dialogs():
    return [
        Dialog(
            windows.main_menu_window(),
            windows.address_book_entry_window(),
            windows.enter_value_window(text="Dialog started by {started_by}\n"
                                            "👇 Enter account address 👇",
                                       handler=events.account_address_handler,
                                       state=states.MainMenuStates.enter_account_address,
                                       getter=getters.get_started_by),
            windows.enter_value_window(text="Dialog started by {started_by}\n"
                                            "👇 Enter account alias (Short human readable name) 👇",
                                       handler=events.account_alias_handler,
                                       state=states.MainMenuStates.enter_account_alias,
                                       getter=getters.get_started_by),
            windows.enter_value_window(text="Dialog started by {started_by}\n"
                                            "👇 Enter threshold value, float value in range 0-100 👇",
                                       handler=events.threshold_handler,
                                       state=states.MainMenuStates.enter_native_threshold,
                                       getter=getters.get_started_by),
            windows.enter_value_window(text="Dialog started by {started_by}\n"
                                            "👇 Enter threshold value, float value in range 0-100 👇",
                                       handler=events.threshold_handler,
                                       state=states.MainMenuStates.enter_token_threshold,
                                       getter=getters.get_started_by),
            windows.enter_value_window(text="Dialog started by {started_by}\n"
                                            "👇 Enter schedule period: value in range 1-59 minute(s) 👇",
                                       handler=events.schedule_period_handler,
                                       state=states.MainMenuStates.enter_schedule_period,
                                       getter=getters.get_started_by),
            on_start=None,
            on_process_result=None
        )
    ]
