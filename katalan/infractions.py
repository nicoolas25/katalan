from datetime import datetime
import re
import time
from uuid import uuid4
from katalan.bus import EventBus
from katalan.events import (
    EventType,
    ParsingRequestedEvent,
    RadarTriggeredEvent,
    ParsingCompletedEvent,
    InfractionConfirmedEvent,
)


class Infractions:
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.requests = dict()

    def _get_considered_speed(self, measured_speed: int) -> int:
        """
        Speed measurements aren’t that accurate, we’re removing 10% of the measured speed to get a `considered_speed`, and

        Returns:
            int: `considered_speed`
        """
        return int(measured_speed * 0.9)

    def _check_speed_is_above_maximum_speed(
        self, considered_speed: int, maximum_speed: int
    ) -> bool:
        """
        We compare the `considered_speed` against the `maximum_speed` from the Radars' event and if it's strictly higher we request the parsing.
        """
        return considered_speed > maximum_speed

    def on_radar_triggered(self, event: RadarTriggeredEvent):
        considered_speed = self._get_considered_speed(event.measured_speed)
        if self._check_speed_is_above_maximum_speed(
            considered_speed, event.maximum_speed
        ):
            request_id = uuid4()
            self.requests[request_id] = {
                "event": event,
                "considered_speed": considered_speed,
            }
            self.bus.publish(
                ParsingRequestedEvent(request_id=request_id, raw_photo=event.raw_photo)
            )

    def on_parsing_completed(self, event: ParsingCompletedEvent):
        request = self.requests.get(event.request_id)
        if not request:
            raise ValueError(f"Request {event.request_id} not found")
        self.requests.pop(event.request_id)
        self.bus.publish(
            InfractionConfirmedEvent(
                plate_number=event.parsing_result[0].plate_number,
                triggered_at=datetime.now(),
                measured_speed=request["event"].measured_speed,
                considered_speed=request["considered_speed"],
                maximum_speed=request["event"].maximum_speed,
                equipment_id='aa',
            )
        )

    def __enter__(self):
        self.bus.subscribe(EventType.radar_triggered, self.on_radar_triggered)
        self.bus.subscribe(EventType.parsing_completed, self.on_parsing_completed)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bus.unsubscribe(EventType.radar_triggered, self.on_radar_triggered)
