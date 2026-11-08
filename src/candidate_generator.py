
import json
import re
from pathlib import Path
import traceback


# --------------------------------------------------
# 1. DRAMATIC SIGNALS
# --------------------------------------------------

HOOK_KEYWORDS = [
    "betray", "secret", "truth", "murder", "kill",
    "dead", "marry", "wedding", "leave", "stop",
    "why", "what", "no", "never", "impossible",
    "how could", "you lied", "look at", "help me",
    "who are you", "what happened"
]

CLIFFHANGER_KEYWORDS = [
    "but", "unless", "who", "what", "why",
    "not yet", "you have no idea", "the truth",
    "it's not over", "wait", "suddenly",
    "someone", "behind you", "one more thing",
    "what if", "the secret"
]

EMOTION_KEYWORDS = [
    "screaming", "crying", "shocked", "furious",
    "devastated", "betrayed", "terrified",
    "desperate", "sinister", "gloating",
    "threatening", "pleading", "weeping",
    "slaps", "strikes", "attacks", "grabs",
    "reveals", "discovers", "collapses"
]


# --------------------------------------------------
# 2. TIMELINE BUILDER
# --------------------------------------------------

def build_timeline(episode):
    """
    Flatten scenes into a chronological event timeline.
    Overlapping events are preserved.
    """

    timeline = []

    for scene in episode["scenes"]:

        for event in scene["events"]:

            start = event.get("start_seconds")
            end = event.get("end_seconds")

            if start is None:
                continue

            timeline.append({
                "episode_number": episode["episode_number"],
                "scene_number": scene["scene_number"],
                "scene_heading": scene.get("heading"),
                "event_type": event.get("event_type"),
                "speaker": event.get("speaker"),
                "emotion": event.get("emotion"),
                "start_seconds": start,
                "end_seconds": end,
                "content": event.get("content", "").strip()
            })

    timeline.sort(
        key=lambda x: (
            x["start_seconds"],
            x["end_seconds"] or x["start_seconds"]
        )
    )

    return timeline


# --------------------------------------------------
# 3. TEXT SCORING
# --------------------------------------------------

def count_keyword_matches(text, keywords):
    text = text.lower()

    return sum(
        1 for keyword in keywords
        if keyword in text
    )


def score_hook(event):
    """
    Estimate whether an event could grab attention.
    This is a heuristic, not an LLM judgment.
    """

    text = event["content"].lower()
    score = 0

    score += min(
        count_keyword_matches(text, HOOK_KEYWORDS),
        3
    )

    if "?" in text:
        score += 1

    if "!" in text:
        score += 1

    emotion = (event.get("emotion") or "").lower()

    if any(
        word in emotion
        for word in ["shocked", "angry", "furious",
                     "desperate", "terrified", "betrayed"]
    ):
        score += 1

    if event["event_type"] == "action":
        score += min(
            count_keyword_matches(text, EMOTION_KEYWORDS),
            2
        )

    return min(score, 5)


def score_cliffhanger(event):
    """
    Estimate whether an event could create suspense.
    """

    text = event["content"].lower()
    score = 0

    score += min(
        count_keyword_matches(
            text, CLIFFHANGER_KEYWORDS
        ),
        3
    )

    if "?" in text:
        score += 2

    if "..." in text or "—" in text:
        score += 1

    if any(
        word in text
        for word in ["reveals", "opens the door",
                     "enters", "appears", "discovers"]
    ):
        score += 1

    emotion = (event.get("emotion") or "").lower()

    if any(
        word in emotion
        for word in ["sinister", "ominous", "shocked",
                     "threatening", "desperate"]
    ):
        score += 1

    return min(score, 5)


def score_drama(events):
    """
    Estimate the dramatic intensity within a window.
    """

    score = 0

    for event in events:

        text = (
            event["content"] + " " +
            (event.get("emotion") or "")
        ).lower()

        score += min(
            count_keyword_matches(
                text, EMOTION_KEYWORDS
            ),
            2
        )

    return min(score, 10)


# --------------------------------------------------
# 4. WINDOW EVALUATION
# --------------------------------------------------

def get_window_events(timeline, start, end):

    return [
        event for event in timeline
        if event["start_seconds"] < end
        and (
            event["end_seconds"] is None
            or event["end_seconds"] > start
        )
    ]


def evaluate_window(timeline, start_event, end_event):
    """
    Evaluate one potential promo window.
    """

    start = start_event["start_seconds"]
    end = end_event["end_seconds"]

    if end is None:
        return None

    duration = end - start

    if not 20 <= duration <= 60:
        return None

    events = get_window_events(
        timeline, start, end
    )

    if not events:
        return None

    # Hook must be present in the first three seconds.
    opening_events = [
        event for event in events
        if event["start_seconds"] < start + 3
        and (
            event["end_seconds"] is None
            or event["end_seconds"] > start
        )
    ]

    # Evaluate events close to the ending.
    ending_events = [
        event for event in events
        if event["end_seconds"] is not None
        and event["end_seconds"] >= end - 5
    ]

    hook_score = max(
        (score_hook(event) for event in opening_events),
        default=0
    )

    cliffhanger_score = max(
        (
            score_cliffhanger(event)
            for event in ending_events
        ),
        default=0
    )

    drama_score = score_drama(events)

    # Duration score: reward clips in the middle
    # of the permitted duration range.
    duration_score = max(
        0,
        5 - abs(duration - 40) / 8
    )

    # Preliminary heuristic score.
    preliminary_score = (
        hook_score * 0.30
        + cliffhanger_score * 0.35
        + min(drama_score / 2, 5) * 0.20
        + duration_score * 0.15
    ) * 20

    # Keep promising candidates for further evaluation.
    if (
        hook_score < 1
        and cliffhanger_score < 1
        and drama_score < 2
    ):
        return None

    return {
        "episode_number": start_event["episode_number"],
        "start_seconds": round(start, 2),
        "end_seconds": round(end, 2),
        "duration_seconds": round(duration, 2),
        "start_scene": start_event["scene_number"],
        "end_scene": end_event["scene_number"],
        "hook_score": hook_score,
        "cliffhanger_score": cliffhanger_score,
        "drama_score": drama_score,
        "duration_score": round(duration_score, 2),
        "preliminary_score": round(
            preliminary_score, 2
        ),
        "opening_event": start_event["content"],
        "ending_event": end_event["content"],
        "context_events": [
        {
            "type": event["event_type"],
            "speaker": event.get("speaker"),
            "emotion": event.get("emotion"),
            "start_seconds": event["start_seconds"],
            "end_seconds": event["end_seconds"],
            "content": event["content"]
        }
        for event in events],
        "event_count": len(events)
    }


# --------------------------------------------------
# 5. CANDIDATE GENERATION
# --------------------------------------------------


def generate_candidates(episode):
    """
    Generate possible 20-60 second promo windows
    within one episode.
    """

    timeline = build_timeline(episode)

    candidates = []

    start_events = [
        event for event in timeline
        if score_hook(event) >= 1
    ]

    end_events = [
        event for event in timeline
        if event["end_seconds"] is not None
        and score_cliffhanger(event) >= 1
    ]

    for start_event in start_events:

        for end_event in end_events:

            if (
                end_event["end_seconds"]
                <= start_event["start_seconds"]
            ):
                continue

            candidate = evaluate_window(
                timeline,
                start_event,
                end_event
            )

            # IMPORTANT: Never append None.
            if candidate is None:
                continue

            candidate["episode_logline"] = (
                episode.get("logline", "")
            )

            candidate["continuity_notes"] = (
                episode.get("continuity_notes", "")
            )

            candidates.append(candidate)

    # Defensive filtering before sorting.
    candidates = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict)
        and candidate.get("preliminary_score") is not None
    ]
    print(
    f"Episode {episode['episode_number']}: "
    f"{len(candidates)} valid candidates generated")

    candidates.sort(
        key=lambda x: x["preliminary_score"],
        reverse=True
    )

    return deduplicate_candidates(candidates)



# --------------------------------------------------
# 6. DUPLICATE REMOVAL
# --------------------------------------------------

def calculate_overlap(candidate_a, candidate_b):

    intersection = max(
        0,
        min(
            candidate_a["end_seconds"],
            candidate_b["end_seconds"]
        )
        -
        max(
            candidate_a["start_seconds"],
            candidate_b["start_seconds"]
        )
    )

    shorter_duration = min(
        candidate_a["duration_seconds"],
        candidate_b["duration_seconds"]
    )

    if shorter_duration <= 0:
        return 0

    return intersection / shorter_duration


def deduplicate_candidates(
    candidates,
    overlap_threshold=0.80
):
    """
    Keep higher-scoring candidates when their
    time ranges substantially overlap.
    """

    selected = []

    for candidate in candidates:

        duplicate = False

        for existing in selected:

            same_episode = (
                candidate["episode_number"]
                == existing["episode_number"]
            )

            if not same_episode:
                continue

            overlap = calculate_overlap(
                candidate, existing
            )

            if overlap >= overlap_threshold:
                duplicate = True
                break

        if not duplicate:
            selected.append(candidate)

    for index, candidate in enumerate(selected, 1):
        candidate["candidate_id"] = (
            f"EP{candidate['episode_number']:03d}"
            f"_P{index:03d}"
        )

    return selected


# --------------------------------------------------
# 7. PROCESS ALL EPISODES
# --------------------------------------------------

def process_all_episodes(
    input_dir="data/processed",
    output_dir="data/outputs"
):

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    all_candidates = []

    files = sorted(
        input_path.glob("episode_*.json")
    )

    print(f"Found {len(files)} processed episodes.")

    for file in files:

        try:

            episode = json.loads(
                file.read_text(encoding="utf-8")
            )

            candidates = generate_candidates(
                episode
            )

            all_candidates.extend(candidates)

            print(
                f"Episode {episode['episode_number']}: "
                f"{len(candidates)} candidates"
            )
        

        except Exception as error:

            print(f"\nERROR IN FILE: {file.name}")
            print(f"ERROR MESSAGE: {error}")

            traceback.print_exc()

    all_candidates.sort(
        key=lambda x: x["preliminary_score"],
        reverse=True
    )

    output_file = (
        output_path / "promo_candidates.json"
    )

    output_file.write_text(
        json.dumps(
            all_candidates,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("\n--------------------------------")
    print("CANDIDATE GENERATION COMPLETED")
    print("--------------------------------")
    print(f"Total candidates: {len(all_candidates)}")
    print(f"Saved to: {output_file}")

    return all_candidates


if __name__ == "__main__":

    process_all_episodes()
