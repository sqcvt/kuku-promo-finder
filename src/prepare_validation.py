
import csv
import json
from pathlib import Path

INPUT_PATH = Path("data/outputs/ranked_promos.json")
OUTPUT_PATH = Path("data/outputs/human_validation.csv")


def prepare_validation():

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "rank",
        "candidate_id",
        "episode_number",
        "start_seconds",
        "end_seconds",
        "duration_seconds",
        "combined_score",
        "recommendation",
        "human_relevant",
        "human_quality_score",
        "human_comments"
    ]

    with open(
        OUTPUT_PATH, "w", newline="", encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for candidate in candidates:

            writer.writerow({
                "rank": candidate["rank"],
                "candidate_id": candidate["candidate_id"],
                "episode_number": candidate["episode_number"],
                "start_seconds": candidate["start_seconds"],
                "end_seconds": candidate["end_seconds"],
                "duration_seconds": candidate["duration_seconds"],
                "combined_score": candidate["combined_score"],
                "recommendation": candidate["recommendation"],
                "human_relevant": "",
                "human_quality_score": "",
                "human_comments": ""
            })

    print(f"Validation template created: {OUTPUT_PATH}")
    print(f"Candidates to review: {len(candidates)}")


if __name__ == "__main__":
    prepare_validation()
