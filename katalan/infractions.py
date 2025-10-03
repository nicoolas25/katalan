from katalan.bus import EventBus
from katalan.events import EventType, ParsingRequestedEvent, RadarTriggeredEvent


class Infractions:
    def __init__(self, bus: EventBus):
        self.bus = bus


    def _get_considered_speed(self, measured_speed: int) -> int:
        """
        Speed measurements aren’t that accurate, we’re removing 10% of the measured speed to get a `considered_speed`, and

        Returns:
            int: `considered_speed`
        """
        return int(measured_speed * 0.9)

    def _check_speed_is_above_maximum_speed(self, considered_speed: int, maximum_speed: int) -> bool:
        """
        We compare the `considered_speed` against the `maximum_speed` from the Radars' event and if it's strictly higher we request the parsing.
        """
        return considered_speed > maximum_speed

    def on_radar_triggered(self, event: RadarTriggeredEvent):
        considered_speed = self._get_considered_speed(event.measured_speed)
        if self._check_speed_is_above_maximum_speed(considered_speed, event.maximum_speed):
            self.bus.publish(EventType.parsing_requested, ParsingRequestedEvent(event.raw_photo))

    def __enter__(self):
        self.bus.subscribe(EventType.radar_triggered, self.on_radar_triggered)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass