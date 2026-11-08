
import json
import os
import random
import time

from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from google import genai
from google.genai import types

from src.schemas import PromoEvaluation












# -----------------------------------------
# 1. CONFIGURATION
# -----------------------------------------

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

if not API_KEY:
    raise ValueError("GROQ_API_KEY missing in .env")

client = Groq(api_key=API_KEY)

PROMPT_PATH = Path(
    "prompts/promo_evaluation.txt"
)

INPUT_PATH = Path(
    "data/outputs/promo_candidates.json"
)

CACHE_PATH = Path(
    "data/outputs/groq_evaluation_cache.json"
)

OUTPUT_PATH = Path(
    "data/outputs/groq_evaluated_candidates.json"
)

FAILURE_PATH = Path(
    "data/outputs/groq_evaluation_failures.json"
)


# -----------------------------------------
# 2. SCORING WEIGHTS
# -----------------------------------------

WEIGHTS = {
    "hook_strength": 0.25,
    "cliffhanger_strength": 0.25,
    "standalone_comprehensibility": 0.20,
    "emotional_impact": 0.15,
    "narrative_coherence": 0.10,
    "duration_suitability": 0.05
}


# -----------------------------------------
# 3. LOAD PROMPT
# -----------------------------------------

def load_prompt():

    return PROMPT_PATH.read_text(
        encoding="utf-8"
    )


# -----------------------------------------
# 4. LOAD CACHE
# -----------------------------------------

def load_cache():

    if CACHE_PATH.exists():

        return json.loads(
            CACHE_PATH.read_text(
                encoding="utf-8"
            )
        )

    return {}


def save_cache(cache):

    CACHE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    CACHE_PATH.write_text(
        json.dumps(
            cache,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# -----------------------------------------
# 5. BUILD CANDIDATE CONTEXT
# -----------------------------------------

def build_candidate_prompt(
    candidate,
    base_prompt
):

    context = {
        "candidate_id": candidate["candidate_id"],
        "episode_number": candidate["episode_number"],
        "duration_seconds": candidate["duration_seconds"],
        "start_seconds": candidate["start_seconds"],
        "end_seconds": candidate["end_seconds"],
        "episode_logline": candidate.get(
            "episode_logline", ""
        ),
        "continuity_notes": candidate.get(
            "continuity_notes", ""
        ),
        "events": candidate.get(
            "context_events", []
        )
    }

    return (
    base_prompt
    + "\n\nCANDIDATE DATA:\n"
    + json.dumps(
        context,
        ensure_ascii=False,
        separators=(",", ":")
    )
)


# -----------------------------------------
# 6. CALCULATE WEIGHTED SCORE
# -----------------------------------------

def calculate_ai_score(evaluation):

    score = 0

    for criterion, weight in WEIGHTS.items():

        value = getattr(
            evaluation,
            criterion
        )

        score += value * weight

    return round(score * 20, 2)


# -----------------------------------------
# 7. EVALUATE ONE CANDIDATE
# -----------------------------------------


import random



def evaluate_candidate(candidate, base_prompt):

    prompt = build_candidate_prompt(
        candidate,
        base_prompt
    )

    max_retries = 4

    for attempt in range(max_retries):

        try:

            response = client.chat.completions.create(

                model=MODEL_NAME,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert short-form "
                            "drama advertisement evaluator. "
                            "Evaluate the complete screenplay "
                            "sequence critically and objectively."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "promo_evaluation",
                        "strict": True,
                        "schema": PromoEvaluation.model_json_schema()
                    }
                },

                temperature=0.2,

                max_completion_tokens=2000
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError(
                    "Groq returned an empty response."
                )

            evaluation = PromoEvaluation.model_validate_json(
                content
            )

            ai_score = calculate_ai_score(
                evaluation
            )

            return {
                "candidate_id": candidate["candidate_id"],
                "episode_number": candidate["episode_number"],
                "start_seconds": candidate["start_seconds"],
                "end_seconds": candidate["end_seconds"],
                "duration_seconds": candidate["duration_seconds"],
                "preliminary_score": candidate["preliminary_score"],
                "ai_score": ai_score,
                "provider": "groq",
                "model": MODEL_NAME,
                "evaluation": evaluation.model_dump()
            }

        except Exception as error:

            error_message = str(error).upper()

            # Retry temporary rate limits and server errors.
            retryable = any(
                code in error_message
                for code in [
                    "429",
                    "RATE_LIMIT",
                    "500",
                    "502",
                    "503",
                    "504",
                    "TIMEOUT"
                ]
            )

            if not retryable or attempt == max_retries - 1:
                raise

            wait_time = min(
                5 * (2 ** attempt),
                60
            ) + random.uniform(0, 2)

            print(
                f"Temporary Groq error: {error}"
            )

            print(
                f"Retrying in {wait_time:.1f} seconds..."
            )

            time.sleep(wait_time)




# -----------------------------------------
# 8. EVALUATE ALL CANDIDATES
# -----------------------------------------

def evaluate_all_candidates():
    import json
    import time
    from pathlib import Path

    candidates_path = Path("data/outputs/filtered_candidates.json")

    CACHE_PATH = Path("data/outputs/groq_evaluation_cache.json")
    OUTPUT_PATH = Path("data/outputs/groq_evaluated_candidates.json")
    FAILURE_PATH = Path("data/outputs/groq_evaluation_failures.json")

    # Load candidates
    with open(candidates_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    # Load existing cache
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    else:
        cache = {}

    # Load existing failures
    failures = []

    print(f"Total candidates: {len(candidates)}")
    print(f"Already evaluated: {len(cache)}")

    # Skip previously evaluated candidates
    remaining_candidates = [
        c for c in candidates
        if c["candidate_id"] not in cache
    ]

    print(f"Remaining candidates: {len(remaining_candidates)}")

    PROMPT_PATH = Path("prompts/promo_evaluation.txt")

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        base_prompt = f.read()

    for index, candidate in enumerate(remaining_candidates, start=1):
        candidate_id = candidate["candidate_id"]

        print(
            f"\n[{index}/{len(remaining_candidates)}] "
            f"Evaluating {candidate_id}"
        )

        try:
            result = evaluate_candidate(candidate,base_prompt)

            if result is None:
                raise ValueError("Evaluator returned None")

            cache[candidate_id] = result

            # Save cache immediately after success
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)

            print(
    f"Success | AI Score: {result.get('ai_score', 'N/A')} | "
    f"Recommendation: {result.get('evaluation', {}).get('recommendation', 'N/A')}"
)

            # Small delay between API requests
            time.sleep(2)

        except Exception as e:
            print(f"Failed: {candidate_id} | {str(e)}")

            failures.append({
                "candidate_id": candidate_id,
                "error": str(e)
            })

            # Save failures immediately
            with open(FAILURE_PATH, "w", encoding="utf-8") as f:
                json.dump(failures, f, indent=2, ensure_ascii=False)

            # Stop if quota is exhausted
            error_message = str(e).lower()

            if (
                "quota" in error_message
                or "rate_limit" in error_message
                or "resource_exhausted" in error_message
            ):
                print("\nAPI quota/rate limit reached. Stopping.")
                break

    # Generate final successful evaluation output
    evaluated_candidates = [
    cache[c["candidate_id"]]
    for c in candidates
    if c["candidate_id"] in cache
]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            evaluated_candidates,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\n========== EVALUATION SUMMARY ==========")
    print(f"Total candidates: {len(candidates)}")
    print(f"Successfully evaluated: {len(cache)}")
    print(f"Remaining: {len(candidates) - len(cache)}")
    print(f"New failures: {len(failures)}")
    print(f"Output saved: {OUTPUT_PATH}")
    print("========================================")

if __name__ == "__main__":
    evaluate_all_candidates()