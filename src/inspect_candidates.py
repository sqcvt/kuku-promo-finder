
import json
from pathlib import Path


file_path = Path(
    "data/outputs/promo_candidates.json"
)

candidates = json.loads(
    file_path.read_text(encoding="utf-8")
)

print(f"\nTotal candidates: {len(candidates)}")

print("\nTOP 10 PROMO CANDIDATES")
print("=" * 70)

for candidate in candidates[:10]:

    print(
        f"\nID: {candidate['candidate_id']}"
    )

    print(
        f"Episode: {candidate['episode_number']}"
    )

    print(
        f"Start: {candidate['start_seconds']} sec"
    )

    print(
        f"End: {candidate['end_seconds']} sec"
    )

    print(
        f"Duration: {candidate['duration_seconds']} sec"
    )

    print(
        f"Hook score: {candidate['hook_score']}/5"
    )

    print(
        f"Cliffhanger score: "
        f"{candidate['cliffhanger_score']}/5"
    )

    print(
        f"Preliminary score: "
        f"{candidate['preliminary_score']}/100"
    )

    print(
        f"Opening: {candidate['opening_event']}"
    )

    print(
        f"Ending: {candidate['ending_event']}"
    )

    print("-" * 70)
