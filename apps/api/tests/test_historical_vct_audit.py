import csv
import importlib.util
from pathlib import Path


def test_historical_audit_retains_literal_nan_and_flags_aggregate_duplicates(tmp_path):
    module_path = Path(__file__).resolve().parents[3] / "scripts/audit_historical_vct.py"
    spec = importlib.util.spec_from_file_location("historical_audit", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "history.csv"
    rows = [
        {"Player": "nan", "Map": "2 Bind", "Agent": "Omen", "Side": "both"},
        {"Player": "nan", "Map": "All Maps", "Agent": "", "Side": "both"},
    ]
    with source.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows([*rows, rows[0]])
    report = module.audit(source)
    assert report["distinct_display_names"] == 1
    assert report["all_maps_summary_rows"] == 1
    assert report["map_labels"] == ["Bind"]
    assert report["exact_duplicate_rows"] == 1
    assert report["missing_counts"]["Agent"] == 1
    assert report["playstyle_label_status"] == "not_available"
