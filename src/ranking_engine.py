
import json
import csv
from pathlib import Path


# -----------------------------------------
# 1. CONFIGURATION
# -----------------------------------------

INPUT_PATH = Path(
    "data/outputs/groq_evaluated_candidates.json"
)

OUTPUT_JSON = Path(
    "data/outputs/ranked_promos.json"
)

OUTPUT_CSV = Path(
    "data/outputs/ranked_promos.csv"
)

PRELIMINARY_WEIGHT = 0.30
AI_WEIGHT = 0.70

# Minimum overlap relative to the shorter clip
OVERLAP_THRESHOLD = 0.50


# -----------------------------------------
# 2. LOAD EVALUATED CANDIDATES
# -----------------------------------------

def load_candidates():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}"
        )

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    if isinstance(candidates, dict):
        candidates = list(candidates.values())

    print(f"Loaded candidates: {len(candidates)}")

    return candidates


# -----------------------------------------
# 3. CALCULATE COMBINED SCORE
# -----------------------------------------

def calculate_combined_score(candidate):

    preliminary_score = candidate.get(
        "preliminary_score", 0
    )

    ai_score = candidate.get(
        "ai_score", 0
    )

    return round(
        PRELIMINARY_WEIGHT * preliminary_score
        + AI_WEIGHT * ai_score,
        2
    )


# -----------------------------------------
# 4. EXTRACT RECOMMENDATION
# -----------------------------------------

def extract_recommendation(candidate):

    evaluation = candidate.get("evaluation", {})

    return evaluation.get(
        "recommendation", "unknown"
    )


# -----------------------------------------
# 5. CHECK CLIP OVERLAP
# -----------------------------------------

def calculate_overlap_ratio(candidate1, candidate2):

    start1 = candidate1["start_seconds"]
    end1 = candidate1["end_seconds"]

    start2 = candidate2["start_seconds"]
    end2 = candidate2["end_seconds"]

    overlap = max(
        0,
        min(end1, end2) - max(start1, start2)
    )

    duration1 = end1 - start1
    duration2 = end2 - start2

    shorter_duration = min(duration1, duration2)

    if shorter_duration <= 0:
        return 0

    return overlap / shorter_duration


# -----------------------------------------
# 6. REMOVE DUPLICATE / OVERLAPPING CLIPS
# -----------------------------------------

def remove_overlapping_candidates(candidates):

    # Highest scoring candidates are considered first
    candidates = sorted(
        candidates,
        key=lambda x: x["combined_score"],
        reverse=True
    )

    selected = []

    for candidate in candidates:

        is_duplicate = False

        for existing in selected:

            # Compare clips only from the same episode
            if (
                candidate["episode_number"]
                != existing["episode_number"]
            ):
                continue

            overlap_ratio = calculate_overlap_ratio(
                candidate,
                existing
            )

            if overlap_ratio >= OVERLAP_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            selected.append(candidate)

    print(
        f"Candidates after overlap removal: {len(selected)}"
    )

    return selected


# -----------------------------------------
# 7. PREPARE FINAL RANKED DATA
# -----------------------------------------

def prepare_ranked_candidates(candidates):

    ranked = []

    for candidate in candidates:

        evaluation = candidate.get("evaluation", {})

        result = {
            "candidate_id": candidate["candidate_id"],
            "episode_number": candidate["episode_number"],
            "start_seconds": candidate["start_seconds"],
            "end_seconds": candidate["end_seconds"],
            "duration_seconds": candidate["duration_seconds"],

            "preliminary_score": candidate.get(
                "preliminary_score", 0
            ),

            "ai_score": candidate.get(
                "ai_score", 0
            ),

            "combined_score": calculate_combined_score(
                candidate
            ),

            "recommendation": extract_recommendation(
                candidate
            ),

            "why_it_works": evaluation.get(
                "why_it_works", ""
            ),

            "weaknesses": evaluation.get(
                "weaknesses", []
            ),

            "evidence_from_script": evaluation.get(
                "evidence_from_script", []
            )
        }

        ranked.append(result)

    return ranked


# -----------------------------------------
# 8. SAVE JSON OUTPUT
# -----------------------------------------

def save_json(candidates):

    OUTPUT_JSON.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:

        json.dump(
            candidates,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"JSON saved: {OUTPUT_JSON}")


# -----------------------------------------
# 9. SAVE CSV OUTPUT
# -----------------------------------------

def save_csv(candidates):

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not candidates:
        print("No candidates available for CSV.")
        return

    fieldnames = list(candidates[0].keys())

    with open(
        OUTPUT_CSV,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for candidate in candidates:

            row = candidate.copy()

            row["weaknesses"] = json.dumps(
                row["weaknesses"],
                ensure_ascii=False
            )

            row["evidence_from_script"] = json.dumps(
                row["evidence_from_script"],
                ensure_ascii=False
            )

            writer.writerow(row)

    print(f"CSV saved: {OUTPUT_CSV}")


# -----------------------------------------
# 10. MAIN PIPELINE
# -----------------------------------------

def run_ranking_pipeline():

    print("\n========== PHASE 4 ==========")

    candidates = load_candidates()

    # Calculate scores and prepare fields
    ranked = prepare_ranked_candidates(candidates)

    # Remove overlapping clips
    ranked = remove_overlapping_candidates(ranked)

    # Sort by combined score
    ranked.sort(
        key=lambda x: x["combined_score"],
        reverse=True
    )

    # Assign final ranks
    for rank, candidate in enumerate(ranked, start=1):
        candidate["rank"] = rank

    # Save outputs
    save_json(ranked)
    save_csv(ranked)

    print("\n========== TOP 10 PROMOS ==========")

    for candidate in ranked[:10]:

        print(
            f"Rank {candidate['rank']} | "
            f"{candidate['candidate_id']} | "
            f"Score: {candidate['combined_score']} | "
            f"Recommendation: {candidate['recommendation']}"
        )

    print("\nRanking pipeline completed.")


if __name__ == "__main__":
    run_ranking_pipeline()
