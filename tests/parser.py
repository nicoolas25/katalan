from katalan.bus import EventBus
from katalan.events import EventType, ParsingCompletedEvent, ParsingRequestedEvent


class Parser:
    """
    Represent a fake photo parser in the system.

    We don't own the real ones, we just listen to events and configure pre-defined replies.
    """

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._configured_responses: dict[
            bytes, list[ParsingCompletedEvent.PlateNumberParsing]
        ] = {}

    def on(
        self,
        raw_photo: bytes,
        parsing_result: list[ParsingCompletedEvent.PlateNumberParsing],
    ) -> None:
        self._configured_responses[raw_photo] = parsing_result

    def _on_parsing_requested(self, event: ParsingRequestedEvent) -> None:
        if parsing_result := self._configured_responses.get(event.raw_photo):
            self._bus.publish(
                event=ParsingCompletedEvent(
                    request_id=event.request_id,
                    parsing_result=parsing_result,
                ),
            )

    def __enter__(self) -> "Parser":
        self._bus.subscribe(
            event_type=EventType.parsing_requested,
            listener=self._on_parsing_requested,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._bus.unsubscribe(
            event_type=EventType.parsing_requested,
            listener=self._on_parsing_requested,
        )
