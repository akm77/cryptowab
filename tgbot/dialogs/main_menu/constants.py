from enum import Enum


class MainMenu(str, Enum):
    NEW_WALLET = "mm01"
    WALLET_ITEMS = "mm02"
    WALLET_ITEMS_SCROLLING_GROUP = "mm03"
    ENTER_WALLET_ADDRESS = "mm04"

    def __str__(self) -> str:
        return str.__str__(self)
