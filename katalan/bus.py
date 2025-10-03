from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from katalan.events import Event, EventType

E = TypeVar("E", contravariant=True, bound="Event")


class Listener(Protocol[E]):
    def __call__(self, event: E) -> None: ...


class EventBus:
    listeners: dict["EventType", set[Listener]]

    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_type: "EventType", listener: Listener):
        if event_type not in self.listeners:
            self.listeners[event_type] = set()

        self.listeners[event_type].add(listener)

    def unsubscribe(self, event_type: "EventType", listener: Listener):
        if event_type in self.listeners:
            self.listeners[event_type].discard(listener)

    def publish(self, event: "Event"):
        for listener_fn in self.listeners.get(event.event_type, {}):
            listener_fn(event=event)
