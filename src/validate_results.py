
import csv
import json
from pathlib import Path

INPUT_PATH = Path("data/outputs/human_validation.csv")
OUTPUT_PATH = Path("data/outputs/phase6_metrics.json")

K_VALUES = [5, 10, 20]


def load_validation_data():

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    validated = []

    for row in rows:

        if row["human_relevant"].strip() not in ["0", "1"]:
            continue

        row["human_relevant"] = int(row["human_relevant"])
        row["combined_score"] = float(row["combined_score"])

        validated.append(row)

    return sorted(
        validated,
        key=lambda x: x["combined_score"],
        reverse=True
    )


def calculate_precision_recall(rows, k):

    top_k = rows[:k]

    if not top_k:
        return 0.0, 0.0

    relevant_in_top_k = sum(
        row["human_relevant"] for row in top_k
    )

    total_relevant = sum(
        row["human_relevant"] for row in rows
    )

    precision = relevant_in_top_k / len(top_k)

    recall = (
        relevant_in_top_k / total_relevant
        if total_relevant > 0
        else 0.0
    )

    return round(precision, 4), round(recall, 4)


def calculate_quality_metrics(rows):

    quality_scores = []

    for row in rows:

        score = row["human_quality_score"].strip()

        if score:
            value = float(score)

            if 1 <= value <= 5:
                quality_scores.append(value)

    if not quality_scores:
        return None

    return round(
        sum(quality_scores) / len(quality_scores), 2
    )


def calculate_recommendation_distribution(rows):

    distribution = {
        "strong": 0,
        "moderate": 0,
        "weak": 0,
        "unknown": 0
    }

    for row in rows:

        recommendation = row["recommendation"].lower()

        if recommendation in distribution:
            distribution[recommendation] += 1
        else:
            distribution["unknown"] += 1

    return distribution


def run_validation():

    rows = load_validation_data()

    if not rows:
        print("No human-annotated candidates found.")
        return

    total = len(rows)

    total_relevant = sum(
        row["human_relevant"] for row in rows
    )

    total_irrelevant = total - total_relevant

    results = {
        "total_annotated": total,
        "relevant_candidates": total_relevant,
        "irrelevant_candidates": total_irrelevant,
        "overall_precision": round(
            total_relevant / total, 4
        ),
        "precision_recall_at_k": {},
        "average_human_quality_score":
            calculate_quality_metrics(rows),
        "recommendation_distribution":
            calculate_recommendation_distribution(rows)
    }

    for k in K_VALUES:

        precision, recall = calculate_precision_recall(
            rows, min(k, total)
        )

        results["precision_recall_at_k"][str(k)] = {
            "precision": precision,
            "recall": recall
        }

    OUTPUT_PATH.parent.mkdir(
        parents=True, exist_ok=True
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n========== PHASE 6 RESULTS ==========")
    print(f"Annotated candidates: {total}")
    print(f"Relevant: {total_relevant}")
    print(f"Irrelevant: {total_irrelevant}")

    for k, metrics in results["precision_recall_at_k"].items():

        print(
            f"Precision@{k}: {metrics['precision']:.2%} | "
            f"Recall@{k}: {metrics['recall']:.2%}"
        )

    print(
        "Average human quality score:",
        results["average_human_quality_score"]
    )

    print(f"\nMetrics saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    run_validation()
