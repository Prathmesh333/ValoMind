"""Regenerate the implemented contract from the repository root."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))

from valomind.main import create_app

target = ROOT / "packages/contracts/openapi.json"
target.write_text(json.dumps(create_app().openapi(), indent=2) + "\n", encoding="utf-8")
