"""Package visually inspected HUD box proposals; never label them verified automatically."""

import csv
import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results/hud_seed_v1"
CLASSES = [
    "scoreboard",
    "current_map_label",
    "team_label",
    "roster_row",
    "roster_player_name",
    "roster_agent_portrait",
]


def boxes(second):
    result = [
        (0, (640, 0, 1270, 84)),
        (1, (22, 0, 159, 25)),
        (2, (725, 5, 783, 44)),
        (2, (1139, 5, 1188, 44)),
    ]
    if second == 10:
        for i in range(5):
            y = 783 + i * 56
            result.extend(
                [
                    (3, (15, y, 953, y + 53)),
                    (3, (968, y, 1906, y + 53)),
                    (4, (647, y + 5, 808, y + 38)),
                    (4, (1170, y + 5, 1275, y + 38)),
                    (5, (573, y, 641, y + 53)),
                    (5, (1276, y, 1348, y + 53)),
                ]
            )
    else:
        for i in range(5):
            y = 550 + i * 106
            result.extend(
                [
                    (3, (16, y, 329, min(1065, y + 90))),
                    (3, (1593, y, 1907, min(1065, y + 90))),
                    (4, (80, y + 7, 250, y + 35)),
                    (4, (1734, y + 7, 1841, y + 35)),
                    (5, (17, y, 76, y + 47)),
                    (5, (1841, y, 1905, y + 47)),
                ]
            )
    return result


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    proposals = []
    for second in [10, 30, 90]:
        split = "val" if second == 90 else "train"
        image_dir = OUTPUT / "images" / split
        label_dir = OUTPUT / "labels" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        stem = f"omjZXmc7_4A_{second:04d}"
        shutil.copyfile(ROOT / f"results/review/frame_{second}.jpg", image_dir / f"{stem}.jpg")
        lines = []
        for index, (class_id, (x1, y1, x2, y2)) in enumerate(boxes(second)):
            if not 0 <= x1 < x2 <= 1920 or not 0 <= y1 < y2 <= 1080:
                raise ValueError("Box outside inspected 1920x1080 frame")
            lines.append(
                f"{class_id} {(x1 + x2) / 3840:.8f} {(y1 + y2) / 2160:.8f} "
                f"{(x2 - x1) / 1920:.8f} {(y2 - y1) / 1080:.8f}"
            )
            proposals.append(
                {
                    "image": f"images/{split}/{stem}.jpg",
                    "box_id": index,
                    "class_name": CLASSES[class_id],
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "source_video_id": "omjZXmc7_4A",
                    "timestamp_ms": second * 1000,
                    "status": "proposed",
                    "method": "assistant_visual_seed",
                    "reviewer_id": "",
                }
            )
        (label_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (OUTPUT / "review.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(proposals[0]))
        writer.writeheader()
        writer.writerows(proposals)
    yaml = "# PROPOSED labels. Review before training. Same-video validation is smoke-only.\n"
    yaml += "train: images/train\nval: images/val\nnames:\n"
    yaml += "".join(f"  {i}: {name}\n" for i, name in enumerate(CLASSES))
    (OUTPUT / "candidate.yaml").write_text(yaml, encoding="utf-8")
    (OUTPUT / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "hud_seed_v1",
                "source_url": "https://youtu.be/omjZXmc7_4A",
                "source_rights_status": "unconfirmed",
                "is_synthetic": False,
                "label_status": "proposed",
                "image_size": [1920, 1080],
                "images": 3,
                "boxes": len(proposals),
                "classes": CLASSES,
                "validation_scope": "Same-video smoke test only; not independent evaluation",
                "label_version": "assistant_visual_seed_v1",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (OUTPUT / "README.txt").write_text(
        "DRAFT HUD DATASET: 3 inspected frames, proposed approximate boxes.\n"
        "Review in a YOLO annotation editor; correct every box and missing instance.\n"
        "Classes refer only to broadcast HUD regions, not world labels/facecam text.\n"
        "Player and character identities are NOT detection classes.\n"
        "The 10s frame uses a buy-phase layout; 30s/90s use sidebar layouts.\n"
        "A scoreboard detector alone is insufficient to distinguish replay from gameplay.\n"
        "No filler/replay/negative examples included. Do not claim useful trained accuracy.\n"
        "candidate.yaml is a smoke-test layout; train/val share source and rounds.\n"
        "Use independently reviewed labels from other broadcasts for real evaluation.\n",
        encoding="utf-8",
    )
    archive = OUTPUT.with_suffix(".zip")
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
        for path in sorted(OUTPUT.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(OUTPUT))
    print(f"Created {archive}: 3 images, {len(proposals)} proposed boxes")


if __name__ == "__main__":
    main()
