from typing import Iterator

import pytest

from katalan.bus import EventBus
from katalan.events import Event, EventType
from katalan.infractions import Infractions
from tests.parser import Parser
from tests.radars import Radar


@pytest.fixture(autouse=True, scope="function")
def bus() -> EventBus:
    return EventBus()


@pytest.fixture(autouse=True, scope="function")
def radar(bus: EventBus) -> Radar:
    return Radar(maximum_speed=100, bus=bus)


@pytest.fixture
def parser(bus: EventBus) -> Iterator[Parser]:
    with Parser(bus=bus) as parser:
        yield parser

@pytest.fixture
def infractions(bus: EventBus) -> Iterator[Infractions]:
    with Infractions(bus=bus) as infractions:
        yield infractions


class EventHistory:
    def __init__(self):
        self._all_events = []

    def get_events(self, event_type: EventType | None = None) -> list[Event]:
        return [
            event
            for event in self._all_events
            if event_type is None or event.event_type == event_type
        ]

    def clear_events(self) -> None:
        self._all_events.clear()

    def _record_event(self, event: Event) -> None:
        self._all_events.append(event)


@pytest.fixture
def event_history(bus: EventBus) -> Iterator[EventHistory]:
    history = EventHistory()

    for event_type in EventType:
        bus.subscribe(
            event_type=event_type,
            listener=history._record_event,
        )

    try:
        yield history

    finally:
        for event_type in EventType:
            bus.unsubscribe(
                event_type=event_type,
                listener=history._record_event,
            )
