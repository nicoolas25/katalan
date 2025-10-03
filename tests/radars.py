from datetime import datetime
from uuid import uuid4

from katalan import SYSTEM_TIME_ZONE
from katalan.bus import EventBus
from katalan.events import RadarTriggeredEvent


class Radar:
    """
    Represent a fake Radar in the system.

    We don't own the real ones, we just receive events from them, so this is about simplifying tests.

    See the tests to understand how to use it.
    """

    def __init__(self, maximum_speed: int, bus: EventBus) -> None:
        self._timezone = SYSTEM_TIME_ZONE
        self._bus = bus
        self._internal_id = uuid4()
        self.equipment_id = f"radar_{self._internal_id}"
        self.maximum_speed = maximum_speed

    def trigger(
        self,
        measured_speed: int,
        raw_photo: bytes,
        triggered_at: datetime | None = None,
    ) -> None:
        self._bus.publish(
            event=RadarTriggeredEvent(
                equipment_id=self.equipment_id,
                triggered_at=triggered_at or datetime.now(self._timezone),
                measured_speed=measured_speed,
                maximum_speed=self.maximum_speed,
                raw_photo=raw_photo,
            ),
        )
