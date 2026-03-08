from enum import Enum, auto


class States(Enum):
    IDLE = auto()
    WAITING_TOPUP_DESCRIPTION = auto()
    WAITING_TOPUP_CATEGORY = auto()
    WAITING_EXPENSE_DESCRIPTION = auto()
    WAITING_EXPENSE_CATEGORY = auto()
    SETTINGS = auto()
