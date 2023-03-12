from enum import Enum


class MainMenu(str, Enum):
    NEW_ACCOUNT = "mm01"
    ADDRESS_BOOK = "mm02"
    ADDRESS_BOOK_SCROLLING_GROUP = "mm03"
    ENTER_ACCOUNT_ADDRESS = "mm04"
    SHOW_TOKEN_TRNS_BUTTON = "mm05"
    SHOW_NATIVE_TRNS_BUTTON = "mm06"
    BACK_TO_ACCOUNTS = "mm07"
    EDIT_ACCOUNT_ALIAS_BUTTON  = "mm08"

    def __str__(self) -> str:
        return str.__str__(self)
