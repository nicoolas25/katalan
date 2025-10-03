from datetime import datetime
from enum import Enum
from typing import ClassVar

import attrs


class EventType(Enum):
    radar_triggered = "radar_triggered"
    parsing_requested = "parsing_requested"
    parsing_completed = "parsing_completed"
    infraction_confirmed = "infraction_confirmed"


@attrs.define(frozen=True, kw_only=True)
class Event:
    """
    Base class for all events. Will be subclassed for specific events...
    """

    event_type: ClassVar[EventType]


@attrs.define(frozen=True, kw_only=True)
class RadarTriggeredEvent(Event):
    equipment_id: str
    triggered_at: datetime
    measured_speed: int
    maximum_speed: int
    raw_photo: bytes
    event_type = EventType.radar_triggered


@attrs.define(frozen=True, kw_only=True)
class ParsingRequestedEvent(Event):
    request_id: str
    raw_photo: bytes
    event_type = EventType.parsing_requested


@attrs.define(frozen=True, kw_only=True)
class ParsingCompletedEvent(Event):
    @attrs.define(frozen=True, kw_only=True)
    class PlateNumberParsing:
        plate_number: str
        confidence: float

    request_id: str
    parsing_result: list[PlateNumberParsing]
    event_type = EventType.parsing_completed


@attrs.define(frozen=True, kw_only=True)
class InfractionConfirmedEvent(Event):
    plate_number: str
    triggered_at: datetime
    measured_speed: int
    considered_speed: int
    maximum_speed: int
    equipment_id: str
    event_type = EventType.infraction_confirmed
