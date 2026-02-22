from enum import Enum


class PositionType(str, Enum):
    COVERED_CALL = "COVERED_CALL"
    CASH_SECURED_PUT = "CASH_SECURED_PUT"


class PositionStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class PositionOutcome(str, Enum):
    EXPIRED = "EXPIRED"
    ASSIGNED = "ASSIGNED"
    CLOSED_EARLY = "CLOSED_EARLY"
    ROLLED = "ROLLED"


class Broker(str, Enum):
    ROBINHOOD = "robinhood"
    MERRILL = "merrill"
    OTHER = "other"
