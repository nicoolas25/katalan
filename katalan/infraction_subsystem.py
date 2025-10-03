from datetime import datetime
from uuid import uuid4

import attrs

from katalan.bus import EventBus
from katalan.errors import ConfigurationError, PendingBusInteraction
from katalan.events import (
    EventType,
    InfractionConfirmedEvent,
    ParsingCompletedEvent,
    ParsingRequestedEvent,
    RadarTriggeredEvent,
)

RequestId = str


@attrs.define(frozen=True, kw_only=True)
class _ParsingRequestData:
    """
    The data the InfractionSubsystem is responsible to keep while waiting from the parsing_completed event.

    We try to limit it, and not include the raw_photo from the RadarTriggeredEvent which might take a lot of memory
    but won't be useful anymore.
    """

    triggered_at: datetime
    measured_speed: int
    maximum_speed: int
    considered_speed: int
    equipment_id: str


_MEASUREMENT_ERROR_RATE = 0.9
_MINIMUM_RELEVANCE_THRESHOLD = 0.3
_MINIMUM_CONFIDENCE_REQUIREMENT = 0.9


class InfractionSubsystem:
    def __init__(self):
        self._bus: EventBus | None = None
        self._parsing_requests: dict[RequestId, _ParsingRequestData] = dict()

    def _handle_radar_triggered(self, event: RadarTriggeredEvent) -> None:
        assert self._bus, "Bus should be configured to call _handle_radar_triggered"

        considered_speed = int(event.measured_speed * _MEASUREMENT_ERROR_RATE)

        if considered_speed > event.maximum_speed:
            request_id = str(uuid4())

            self._parsing_requests[request_id] = _ParsingRequestData(
                triggered_at=event.triggered_at,
                measured_speed=event.measured_speed,
                maximum_speed=event.maximum_speed,
                considered_speed=considered_speed,
                equipment_id=event.equipment_id,
            )

            self._bus.publish(
                ParsingRequestedEvent(
                    request_id=request_id,
                    raw_photo=event.raw_photo,
                )
            )

    def _handle_parsing_completed(self, event: ParsingCompletedEvent) -> None:
        assert self._bus, "Bus should be configured to call _handle_parsing_completed"

        if parsing_request_data := self._parsing_requests.get(event.request_id):
            if plate_number := _get_unambiguous_plate_number(
                parsing_result=event.parsing_result,
            ):
                self._bus.publish(
                    InfractionConfirmedEvent(
                        plate_number=plate_number,
                        triggered_at=parsing_request_data.triggered_at,
                        measured_speed=parsing_request_data.measured_speed,
                        maximum_speed=parsing_request_data.maximum_speed,
                        considered_speed=parsing_request_data.considered_speed,
                        equipment_id=parsing_request_data.equipment_id,
                    )
                )

    # Infrastructure

    def plug_to_bus(self, bus: EventBus) -> None:
        if self._bus is not None:
            raise ConfigurationError(
                "This InfractionSubsystem is already plugged to a bus"
            )

        self._bus = bus
        self._bus.subscribe(
            event_type=EventType.radar_triggered,
            listener=self._handle_radar_triggered,
        )
        self._bus.subscribe(
            event_type=EventType.parsing_completed,
            listener=self._handle_parsing_completed,
        )

    def unplug_from_bus(self, drop_pending_operations: bool = False) -> None:
        if self._parsing_requests and not drop_pending_operations:
            raise PendingBusInteraction(
                "Can't unplug from the current bus while operations are pending"
            )

        if self._bus:
            self._bus.unsubscribe(
                event_type=EventType.radar_triggered,
                listener=self._handle_radar_triggered,
            )
            self._bus.unsubscribe(
                event_type=EventType.radar_triggered,
                listener=self._handle_radar_triggered,
            )

        self._parsing_requests = dict()
        self._bus = None


def _get_unambiguous_plate_number(
    parsing_result: list[ParsingCompletedEvent.PlateNumberParsing],
) -> str | None:
    # Trim irrelevant data
    relevant_parsing_result = [
        entry
        for entry in parsing_result
        if entry.confidence >= _MINIMUM_RELEVANCE_THRESHOLD
    ]

    match len(relevant_parsing_result):
        case 0:
            # Nothing relevant on the picture
            return None

        case 1:
            # A single plate number is visible
            if relevant_parsing_result[0].confidence >= _MINIMUM_CONFIDENCE_REQUIREMENT:
                return relevant_parsing_result[0].plate_number
            else:
                return None

        case _:
            # Too many plate numbers in the picture
            return None
