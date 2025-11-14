from jolt import json_to_jolt

def test_basic_scenario():
    data = {
        "scenario": {
            "id": 7,
            "name": "Port Delay",
            "events": [
                {"t": 1, "type": "delay", "days": 2},
                {"t": 2, "type": "delay", "days": 3},
            ],
        }
    }

    out = json_to_jolt(data, root_name="scenario")

    assert "scenario {" in out
    assert "id: 7" in out
    assert "events[2] {" in out
    assert "1, delay, 2" in out
