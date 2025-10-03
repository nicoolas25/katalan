from datetime import datetime
import pytest

from katalan import SYSTEM_TIME_ZONE
from katalan.events import EventType, InfractionConfirmedEvent, ParsingCompletedEvent
from tests.conftest import EventHistory
from tests.parser import Parser
from tests.radars import Radar


@pytest.mark.parametrize(
    "maximum_speed,measured_speed,considered_speed,triggers_event",
    [
        (130, 150, 135, True),   # 10% reduction
        (90, 105, 94, True),     # 10% reduction
        (90, 100, 90, False),    # 10% reduction
    ]
)
def test_considered_speed_is_10_percent_lower_than_measured_speed(
    event_history: EventHistory,
    radar: Radar,
    parser: Parser,
    maximum_speed: int,
    measured_speed: int,
    considered_speed: int,
    triggers_event: bool,
):
    # TODO: Make sure your sub-system is subscribed to the events of the bus (the one from conftest)

    # Configure the behaviour of the parser "agent" on the bus
    parser.on(
        raw_photo=b"photo1",
        parsing_result=[
            ParsingCompletedEvent.PlateNumberParsing(
                plate_number="AB123CD",
                confidence=0.9,
            ),
        ],
    )

    # Trigger an event from the radar
    radar.maximum_speed = maximum_speed
    radar.trigger(
        measured_speed=measured_speed,
        raw_photo=b"photo1",
    )


    # Depending on the triggers_event parameter, result will be different.

    events = event_history.get_events(event_type=EventType.infraction_confirmed)

    if triggers_event:
        assert len(events) == 1
        assert isinstance(events[0], InfractionConfirmedEvent)
        assert events[0].considered_speed == considered_speed

    else:
        assert not events


@pytest.mark.parametrize(
    "parsing_result,triggers_event",
    [
        ( # 1 plate number, high confidence, event published
            [
                ParsingCompletedEvent.PlateNumberParsing(
                    plate_number="AB123CD",
                    confidence=0.9,
                ),
            ],
            True,
        ),
        ( # 1 plate number, low confidence, no event published
            [
                ParsingCompletedEvent.PlateNumberParsing(
                    plate_number="AB123CD",
                    confidence=0.8,
                ),
            ],
            False,
        ),
        ( # 2 plate numbers, high confidence, no event published
            [
                ParsingCompletedEvent.PlateNumberParsing(
                    plate_number="AB123CD",
                    confidence=0.9,
                ),
                ParsingCompletedEvent.PlateNumberParsing(
                    plate_number="EF456GH",
                    confidence=0.9,
                ),
            ],
            False,
        ),
        ( # 2 plate numbers, very low and high confidence, event published
            [
                ParsingCompletedEvent.PlateNumberParsing(
                    plate_number="AB123CD",
                    confidence=0.2,
                ),
                ParsingCompletedEvent.PlateNumberParsing(
                    plate_number="EF456GH",
                    confidence=0.9,
                ),
            ],
            False,
        ),
    ]
)
def test_plate_numbers_count_and_confidence_influence_infraction_confirmed(
    event_history: EventHistory,
    radar: Radar,
    parser: Parser,
    parsing_result: list[ParsingCompletedEvent.PlateNumberParsing],
    triggers_event: bool,
):
    # TODO: Make sure your sub-system is subscribed to the events of the bus (the one from conftest)

    # Configure the behaviour of the parser "agent" on the bus
    parser.on(
        raw_photo=b"photo1",
        parsing_result=parsing_result,
    )

    # Trigger an event from the radar
    radar.trigger(
        measured_speed=150,
        raw_photo=b"photo1",
    )

    # Depending on the triggers_event parameter, result will be different.

    events = event_history.get_events(event_type=EventType.infraction_confirmed)

    if triggers_event:
        assert len(events) == 1
    else:
        assert not events


def test_infraction_forward_radar_information(
    event_history: EventHistory,
    radar: Radar,
    parser: Parser,
):
    # TODO: Make sure your sub-system is subscribed to the events of the bus (the one from conftest)

    # Configure the behaviour of the parser "agent" on the bus
    parser.on(
        raw_photo=b"photo1",
        parsing_result=[
            ParsingCompletedEvent.PlateNumberParsing(
                plate_number="AB123CD",
                confidence=0.9,
            ),
        ],
    )

    # Trigger an event from the radar
    triggered_at = datetime.now(SYSTEM_TIME_ZONE)
    measured_speed = 150
    radar.trigger(
        measured_speed=measured_speed,
        raw_photo=b"photo1",
        triggered_at=triggered_at,
    )

    # Check the event outside of the system
    event, _ = event_history.get_events(event_type=EventType.infraction_confirmed)
    assert isinstance(event, InfractionConfirmedEvent)
    assert event.plate_number == "AB123CD"
    assert event.equipment_id == radar.equipment_id
    assert event.maximum_speed == radar.maximum_speed
    assert event.measured_speed == measured_speed
    assert event.triggered_at == triggered_at
