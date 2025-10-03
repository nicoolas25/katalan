# A Code Kata to play at work...

## Pre-requisites

* Have Python installed (should be the case on your Mac?)
* Be intentional abou the python version you're using
    * `pyenv shell` then pick the proper version
* Create a virtual environment for your dependencies if you like:
    * `python -m venv .venv`
    * `source .venv/bin/activate`
* Manage the dependencies:
    * `pip install -r requirements.txt`

## What to do?

We’re part of the system sending speeding tickets to vehicle going too fast on the road!

### Iteration 1

The overall system is based on a communication `bus`. Multiple sub-sytems are plugged to it
and we'll focus on only one that will orchestrate others and have a bit of logic on its own.

There are 3 sub-systems:
- Radars, that are triggered by car passing in front of them.
- Parser, that can analyze pictures from the radars to extract plate numbers.
- Infraction, that collect Radars events, forward them to Parser, and apply logic along the way.

**Radars** are broadcasting like this…

```json
{
  "event_type": "radar_triggered",
  "equipment_id": "radar_<id>",
  "triggered_at": 1759262884,       // Using unix epoch-based time
  "measured_speed": 96,             // Using Km/h
  "maximum_speed": 80,
  "raw_photo": "<base64>"
}
```

**Parser** is receiving and requests through events, and can analize `raw_photo` and return plate numbers.

It’ll react to events you’ll publish:

```json
{
  "event_type": "parsing_requested",
  "request_id": "<uuid>",
  "raw_photo": "<base64>"
}
```

And will answer by publishing other events:

```json
{
  "event_type": "parsing_completed",
  "request_id": "<uuid>",
  "parsing_result": [
    {
      "plate_number": "AB123CD",
      "confidence": 0.98,
    },
    {
      "plate_number": "EF456GH",
      "confidence": 0.32,
    }
  ]
}
```

The **Infraction** subsystem you'll write will:
- Listen to the event `bus`,
- React to `radar_triggered` events and apply some business logic in order to move forward,
- Publish some `parsing_requested` events to collect the plate numbers of the vehicle(s) that triggered the radar,
- React to `parsing_completed` events and again, run some logic before moving to the next step, and
- Publish some `infraction_confirmed` events for another subsystem.


```json
{
  "event_type": "infraction_confirmed",
  "plate_number": "AB123CD",
  "triggered_at": 1759262884,
  "measured_speed": 96,
  "considered_speed": 87,
  "maximum_speed": 80,
  "equipment_id": "radar_<id>" 
}
```

The business logic deciding if we should (or not) publish a `parsing_requested` event is the following:
- Speed measurements aren’t that accurate, we’re removing 10% of the measured speed to get a `considered_speed`, and
- We compare the `considered_speed` against the `maximum_speed` from the Radars' event and if it's strictly higher we request the parsing.

The business logic deciding if we should (or not) publish a `infraction_confirmed` event is the following:
- We don't consider plate numbers with a `confidence <= 0.3`, we assume they aren't plate numbers at all,
- We don't publish any event if there is multiple plate numbers on the photo,
- We don't publish any event unless `confidence >= 0.9` on the plate number,
- Otherwise, we send the `infraction_confirmed` event.

Another system will pick up the `infraction_confirmed` events, retrieve the owner of the vehicle, and send them the proper speeding ticket...

## Running your test

* Run `pytest` in the root directory
* Run `mypy .` in the root directory
