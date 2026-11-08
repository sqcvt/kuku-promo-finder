
import json
from pathlib import Path
from collections import defaultdict

INPUT_PATH = Path("data/outputs/promo_candidates.json")
OUTPUT_PATH = Path("data/outputs/filtered_candidates.json")

MAX_CANDIDATES = 100
MAX_INITIAL_PER_EPISODE = 2
OVERLAP_THRESHOLD = 0.80


def overlap_ratio(a, b):
    intersection = max(
        0,
        min(a["end_seconds"], b["end_seconds"])
        - max(a["start_seconds"], b["start_seconds"])
    )

    shorter = min(
        a["duration_seconds"],
        b["duration_seconds"]
    )

    return intersection / shorter if shorter > 0 else 0


def is_duplicate(candidate, selected):
    return any(
        candidate["episode_number"] == existing["episode_number"]
        and overlap_ratio(candidate, existing) >= OVERLAP_THRESHOLD
        for existing in selected
    )


def select_candidates():
    candidates = json.loads(
        INPUT_PATH.read_text(encoding="utf-8")
    )

    candidates.sort(
        key=lambda x: x["preliminary_score"],
        reverse=True
    )

    by_episode = defaultdict(list)

    for candidate in candidates:
        by_episode[candidate["episode_number"]].append(candidate)

    selected = []
    selected_ids = set()

    # Pass 1: Select top 2 candidates per episode
    for episode_number in sorted(by_episode):
        count = 0

        for candidate in by_episode[episode_number]:
            if count >= MAX_INITIAL_PER_EPISODE:
                break

            if len(selected) >= MAX_CANDIDATES:
                break

            if is_duplicate(candidate, selected):
                continue

            selected.append(candidate)
            selected_ids.add(candidate["candidate_id"])
            count += 1

    # Pass 2: Fill remaining slots by score
    for candidate in candidates:
        if len(selected) >= MAX_CANDIDATES:
            break

        if candidate["candidate_id"] in selected_ids:
            continue

        if is_duplicate(candidate, selected):
            continue

        selected.append(candidate)
        selected_ids.add(candidate["candidate_id"])

    selected.sort(
        key=lambda x: x["preliminary_score"],
        reverse=True
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_PATH.write_text(
        json.dumps(selected, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Original candidates: {len(candidates)}")
    print(f"Selected candidates: {len(selected)}")
    print(f"Removed candidates: {len(candidates) - len(selected)}")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    select_candidates()
