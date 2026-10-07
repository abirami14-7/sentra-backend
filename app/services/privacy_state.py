from enum import Enum
from typing import Set


class PrivacyState(str, Enum):
    IDLE = "IDLE"
    TRIP_ACTIVE = "TRIP_ACTIVE"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    EMERGENCY_ACTIVE = "EMERGENCY_ACTIVE"
    RESOLVED = "RESOLVED"


ALLOWED_TRANSITIONS = {
    PrivacyState.IDLE: {PrivacyState.TRIP_ACTIVE},
    PrivacyState.TRIP_ACTIVE: {PrivacyState.ANOMALY_DETECTED, PrivacyState.RESOLVED},
    PrivacyState.ANOMALY_DETECTED: {
        PrivacyState.TRIP_ACTIVE,
        PrivacyState.EMERGENCY_ACTIVE,
        PrivacyState.RESOLVED,
    },
    PrivacyState.EMERGENCY_ACTIVE: {PrivacyState.RESOLVED},
    PrivacyState.RESOLVED: {PrivacyState.IDLE},
}


RESOURCE_ACCESS = {
    PrivacyState.IDLE: set(),
    PrivacyState.TRIP_ACTIVE: {"GPS", "LOCATION_HISTORY"},
    PrivacyState.ANOMALY_DETECTED: {"GPS", "LOCATION_HISTORY"},
    PrivacyState.EMERGENCY_ACTIVE: {
        "GPS",
        "LOCATION_HISTORY",
        "EMERGENCY_CONTACTS",
    },
    PrivacyState.RESOLVED: set(),
}


def can_transition(current: str, target: str) -> bool:
    try:
        cur = PrivacyState(current)
        tgt = PrivacyState(target)
    except ValueError:
        return False
    return tgt in ALLOWED_TRANSITIONS.get(cur, set())


def allowed_resources(state: str) -> Set[str]:
    try:
        return RESOURCE_ACCESS.get(PrivacyState(state), set())
    except ValueError:
        return set()
