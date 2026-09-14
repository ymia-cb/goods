from enum import StrEnum

STAFF_CHANNEL = "customer-service:stuff"


class RealTimeOutBoxType(StrEnum):
    MESSAGE_CREATE = "message_created"
    HANDOFF_CHANGE = "handoff_changed"