from enum import Enum


class LogType(str, Enum):
    UNSPECIFIED = "UNSPECIFIED"
    AUTHENTICATION = "AUTHENTICATION"
    ALERT = "ALERT"
    TRADE = "TRADE"
    ORDER = "ORDER"
    ERROR = "ERROR"
    ADMIN = "ADMIN"


class UserSettingsMode(str, Enum):
    DEMO = "DEMO"
    LIVE = "LIVE"


class UserSettingsOrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
