import argparse
import json
import sys
from pathlib import Path

from .encoder import json_to_jolt


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="jolt",
        description="Convert JSON into JOLT tokens."
    )
    parser.add_argument("input", help="JSON input file ('-' for stdin')")
    parser.add_argument("--root", default=None, help="Optional root block name")
    args = parser.parse_args(argv)

    if args.input == "-":
        data = json.load(sys.stdin)
    else:
        p = Path(args.input)
        data = json.loads(p.read_text())

    text = json_to_jolt(data, root_name=args.root)
    sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
