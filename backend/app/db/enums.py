from enum import Enum


class LogType(str, Enum):
    UNSPECIFIED = "unspecified"
    AUTHENTICATION = "authentication"
    ALERT = "alert"
    TRADE = "trade"
    ORDER = "order"
    ERROR = "error"


class UserSettingsMode(str, Enum):
    DEMO = "demo"
    LIVE = "live"
