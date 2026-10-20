import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from evaluate_segment_review import evaluate


def test_evaluation_distinguishes_abstention_and_filler_admission():
    rows = [
        {
            "reference_segment": "gameplay",
            "suggested_segment": "uncertain",
            "processing_action": "review",
            "review_status": "reviewed",
            "reviewer_id": "r",
        },
        {
            "reference_segment": "filler",
            "suggested_segment": "gameplay",
            "processing_action": "extract",
            "review_status": "reviewed",
            "reviewer_id": "r",
        },
    ]
    result = evaluate(rows)
    assert result["missed_match_samples"] == 1
    assert result["admitted_filler_or_replay_samples"] == 1
    assert result["matching_labels"] == 0


def test_evaluation_does_not_score_unreviewed_suggestions():
    with pytest.raises(ValueError, match="No reviewed"):
        evaluate([{"review_status": "pending", "reviewer_id": ""}])
