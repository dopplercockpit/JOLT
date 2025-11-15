import json
from pathlib import Path

from jolt import json_to_jolt


def main() -> None:
    path = Path("examples/scenario.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    json_text = json.dumps(data)
    jolt_text = json_to_jolt(data, root_name="scenario")

    print("JSON length:", len(json_text))
    print("JOLT length:", len(jolt_text))
    print("Ratio (JOLT / JSON):", len(jolt_text) / len(json_text))


if __name__ == "__main__":
    main()
