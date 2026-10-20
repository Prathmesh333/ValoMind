"""Parse existing cloud OCR without rerunning video inference."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workers/analysis"))

from valomind_video.roster import export_rosters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(export_rosters(args.observations, args.output))


if __name__ == "__main__":
    main()
