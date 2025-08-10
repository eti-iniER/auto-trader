from enum import Enum


class LogType(str, Enum):
    UNSPECIFIED = "UNSPECIFIED"
    AUTHENTICATION = "AUTHENTICATION"
    ALERT = "ALERT"
    TRADE = "TRADE"
    ORDER = "ORDER"
    ERROR = "ERROR"


class UserSettingsMode(str, Enum):
    DEMO = "DEMO"
    LIVE = "LIVE"


class UserSettingsOrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
