"""Export one unlabeled portrait per displayed handle/layout from local OCR results."""

import argparse
import csv
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("rosters", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with args.rosters.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    selected = {}
    for row in rows:
        key = (row["video_id"], row["map_id"], row["player_id"], row["layout"])
        if key not in selected:
            selected[key] = row
    review = []
    for row in selected.values():
        name = row["roster_observation_id"] + ".jpg"
        x, y, x2, y2 = [int(row[f"portrait_{axis}"]) for axis in ["x1", "y1", "x2", "y2"]]
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-ss",
                str(int(row["timestamp_ms"]) / 1000),
                "-i",
                str(args.video),
                "-vf",
                f"crop={x2 - x}:{y2 - y}:{x}:{y}",
                "-frames:v",
                "1",
                str(args.output / name),
            ],
            check=True,
        )
        review.append({"image": name, **row, "label_status": "proposed", "reviewer_id": ""})
    if not review:
        raise ValueError("No roster observations found")
    with (args.output / "portrait_review.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(review[0]))
        writer.writeheader()
        writer.writerows(review)
    (args.output / "README.txt").write_text(
        "Unlabeled portrait proposals cropped from reviewed HUD regions.\n"
        "Player/team relationships remain proposals. No character labels inferred.\n"
        "Fill character_agent_id and independently review before using for training.\n"
        "These samples come from one video; they are not a general validation set.\n",
        encoding="utf-8",
    )
    with ZipFile(args.output.with_suffix(".zip"), "w", compression=ZIP_DEFLATED) as archive:
        for path in args.output.iterdir():
            if path.is_file():
                archive.write(path, path.name)
    print(f"Saved {len(review)} portrait proposals to {args.output}")


if __name__ == "__main__":
    main()
