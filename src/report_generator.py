
import json
from pathlib import Path


# -----------------------------------------
# 1. CONFIGURATION
# -----------------------------------------

INPUT_PATH = Path(
    "data/outputs/ranked_promos.json"
)

OUTPUT_JSON = Path(
    "data/outputs/selected_promos.json"
)

OUTPUT_REPORT = Path(
    "data/outputs/promo_report.md"
)

TOP_N = 10


# -----------------------------------------
# 2. LOAD RANKED CANDIDATES
# -----------------------------------------

def load_ranked_candidates():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"File not found: {INPUT_PATH}"
        )

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"Loaded ranked candidates: {len(candidates)}")

    return candidates


# -----------------------------------------
# 3. FORMAT TIMESTAMP
# -----------------------------------------

def format_timestamp(seconds):

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60

    return f"{minutes:02d}:{remaining_seconds:05.2f}"


# -----------------------------------------
# 4. SELECT TOP CANDIDATES
# -----------------------------------------

def select_promos(candidates):

    candidates = sorted(
        candidates,
        key=lambda x: x["combined_score"],
        reverse=True
    )

    selected = candidates[:TOP_N]

    for rank, candidate in enumerate(selected, start=1):
        candidate["selection_rank"] = rank

    print(f"Selected top {len(selected)} promotional clips")

    return selected


# -----------------------------------------
# 5. SAVE SELECTED PROMOS JSON
# -----------------------------------------

def save_selected_promos(selected):

    OUTPUT_JSON.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:

        json.dump(
            selected,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Selected promos saved: {OUTPUT_JSON}")


# -----------------------------------------
# 6. GENERATE MARKDOWN REPORT
# -----------------------------------------

def generate_report(selected, total_candidates):

    report = []

    report.append("# Promotional Clip Selection Report\n")

    report.append("## Project Summary\n")

    report.append(
        f"- Total ranked candidates: {total_candidates}"
    )

    report.append(
        f"- Selected promotional clips: {len(selected)}"
    )

    report.append(
        "- Ranking basis: 30% preliminary score + 70% AI score"
    )

    report.append("\n---\n")

    report.append("## Selected Promotional Clips\n")

    for candidate in selected:

        start = format_timestamp(
            candidate["start_seconds"]
        )

        end = format_timestamp(
            candidate["end_seconds"]
        )

        report.append(
            f"### Rank {candidate['selection_rank']}: "
            f"{candidate['candidate_id']}\n"
        )

        report.append(
            f"- **Episode:** {candidate['episode_number']}"
        )

        report.append(
            f"- **Clip duration:** "
            f"{candidate['duration_seconds']} seconds"
        )

        report.append(
            f"- **Timestamp:** {start} – {end}"
        )

        report.append(
            f"- **Preliminary score:** "
            f"{candidate['preliminary_score']}"
        )

        report.append(
            f"- **AI score:** {candidate['ai_score']}"
        )

        report.append(
            f"- **Combined score:** "
            f"{candidate['combined_score']}"
        )

        report.append(
            f"- **Recommendation:** "
            f"{candidate['recommendation'].upper()}"
        )

        report.append("\n**Why this clip works:**\n")

        report.append(
            candidate.get("why_it_works", "Not available")
        )

        weaknesses = candidate.get("weaknesses", [])

        if weaknesses:

            report.append("\n**Potential weaknesses:**\n")

            for weakness in weaknesses:
                report.append(f"- {weakness}")

        evidence = candidate.get(
            "evidence_from_script", []
        )

        if evidence:

            report.append("\n**Script evidence:**\n")

            for item in evidence:
                report.append(f"- {item}")

        report.append("\n---\n")

    report.append("## Final Notes\n")

    report.append(
        "These clips are selected using automated heuristic "
        "and LLM-based evaluation. Final editorial approval "
        "should include a review of the original screenplay "
        "and video footage."
    )

    OUTPUT_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_REPORT.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print(f"Report generated: {OUTPUT_REPORT}")


# -----------------------------------------
# 7. MAIN PIPELINE
# -----------------------------------------

def run_report_pipeline():

    print("\n========== PHASE 5 ==========")

    candidates = load_ranked_candidates()

    selected = select_promos(candidates)

    save_selected_promos(selected)

    generate_report(
        selected,
        len(candidates)
    )

    print("\n========== TOP PROMOS ==========")

    for candidate in selected:

        print(
            f"Rank {candidate['selection_rank']} | "
            f"{candidate['candidate_id']} | "
            f"Score: {candidate['combined_score']} | "
            f"Recommendation: {candidate['recommendation']}"
        )

    print("\nPhase 5 completed successfully.")


if __name__ == "__main__":
    run_report_pipeline()
