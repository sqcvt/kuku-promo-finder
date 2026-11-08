
import re
import json
from pathlib import Path


TIMESTAMP_PATTERN = r"\d{2}:\d{2}\.\d{2}"

EVENT_HEADER = re.compile(r"^\*\*(.+?):\*\*$")
SCENE_HEADER = re.compile(r"^SCENE\s+(\d+)\s*$", re.IGNORECASE)

TIME_RANGE = re.compile(
    rf"Start:\s*\(({TIMESTAMP_PATTERN})\)"
    rf"(?:\s*\|\s*End:\s*\(({TIMESTAMP_PATTERN})\))?"
)

METADATA_PATTERNS = {
    "episode_number": re.compile(
        r"EPISODE NUMBER:\s*Episode\s*(\d+)", re.I
    ),
    "logline": re.compile(
        r"EPISODE LOGLINE:\s*(.*)", re.I
    ),
    "continuity_notes": re.compile(
        r"CONTINUITY NOTES:\s*(.*)", re.I
    )
}


def timestamp_to_seconds(timestamp):
    """Convert MM:SS.ss into seconds."""

    minutes, remaining = timestamp.split(":")
    return int(minutes) * 60 + float(remaining)


def extract_metadata(text):
    """Extract episode-level information."""

    metadata = {}

    for field, pattern in METADATA_PATTERNS.items():
        match = pattern.search(text)

        if match:
            value = match.group(1).strip()

            if field == "episode_number":
                value = int(value)

            metadata[field] = value

    return metadata


def classify_event(header):
    """Identify the type of screenplay event."""

    normalized = header.strip().upper()

    if normalized == "CAMERA":
        return "camera"

    if normalized == "ACTION":
        return "action"

    if normalized in ("SOUND FX", "SOUND EFFECTS"):
        return "sound"

    if normalized in ("MUSIC", "SCORE"):
        return "music"

    return "dialogue"


def parse_event(header, block, episode_number, scene_number):
    """Parse an individual timestamped screenplay event."""

    match = TIME_RANGE.search(block)

    if not match:
        return None

    start_time = match.group(1)
    end_time = match.group(2)

    # Preserve incomplete events rather than inventing an end time.
    start_seconds = timestamp_to_seconds(start_time)
    end_seconds = (
        timestamp_to_seconds(end_time)
        if end_time else None
    )

    event_type = classify_event(header)

    speaker = None
    emotion = None

    if event_type == "dialogue":
        speaker_match = re.match(
            r"^(.+?)\s*\((.*?)\)\s*$", header
        )

        if speaker_match:
            speaker = speaker_match.group(1).strip()
            emotion = speaker_match.group(2).strip()
        else:
            speaker = header.strip()

    # Remove the timestamp line and retain the description/dialogue.
    content = TIME_RANGE.sub("", block, count=1)

    content = re.sub(
        r"^\s*\*\*.+?:\*\*\s*", "", content
    )

    content = content.strip()

    return {
        "episode_number": episode_number,
        "scene_number": scene_number,
        "event_type": event_type,
        "speaker": speaker,
        "emotion": emotion,
        "start_timestamp": start_time,
        "end_timestamp": end_time,
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "content": content
    }


def parse_scene(scene_text, episode_number, warnings):
    """Parse a single scene and all its events."""

    lines = scene_text.splitlines()

    scene_match = SCENE_HEADER.match(lines[0].strip())

    if not scene_match:
        return None

    scene_number = int(scene_match.group(1))

    heading = None
    scene_start = None
    scene_end = None

    for line in lines[1:]:
        line = line.strip()

        heading_match = re.match(
            r"^Scene\s+heading\s*:\s*(.*)$",
            line,
            re.IGNORECASE
    )

        if heading_match:
            heading = heading_match.group(1).strip()

        elif line.lower().startswith("scene start:"):
            match = re.search(TIMESTAMP_PATTERN, line)
            if match:
                scene_start = match.group()

        elif line.lower().startswith("scene end:"):
            match = re.search(TIMESTAMP_PATTERN, line)
            if match:
                scene_end = match.group()

        elif line.startswith("Scene start:"):
            match = re.search(TIMESTAMP_PATTERN, line)
            if match:
                scene_start = match.group()

        elif line.startswith("Scene end:"):
            match = re.search(TIMESTAMP_PATTERN, line)
            if match:
                scene_end = match.group()

    # Find all event headers.
    event_positions = []

    for index, line in enumerate(lines):
        match = EVENT_HEADER.match(line.strip())

        if match:
            event_positions.append(
                (index, match.group(1).strip())
            )

    events = []

    for i, (start_index, header) in enumerate(event_positions):

        if i + 1 < len(event_positions):
            end_index = event_positions[i + 1][0]
        else:
            end_index = len(lines)

        block = "\n".join(
            lines[start_index:end_index]
        )

        event = parse_event(
            header,
            block,
            episode_number,
            scene_number
        )

        if event is None:
            warnings.append(
                f"Episode {episode_number}, Scene {scene_number}: "
                f"Could not parse event '{header}'"
            )
            continue

        if (
            event["end_seconds"] is not None
            and event["end_seconds"] < event["start_seconds"]
        ):
            warnings.append(
                f"Invalid timestamp range in Episode "
                f"{episode_number}, Scene {scene_number}"
            )

        events.append(event)

    return {
        "scene_number": scene_number,
        "heading": heading,
        "start_timestamp": scene_start,
        "end_timestamp": scene_end,
        "start_seconds": (
            timestamp_to_seconds(scene_start)
            if scene_start else None
        ),
        "end_seconds": (
            timestamp_to_seconds(scene_end)
            if scene_end else None
        ),
        "events": events
    }


def parse_screenplay(file_path):
    """Parse one complete screenplay file."""

    path = Path(file_path)
    text = path.read_text(encoding="utf-8")

    metadata = extract_metadata(text)

    if "episode_number" not in metadata:
        raise ValueError(
            f"Episode number missing in {path.name}"
        )

    warnings = []

    script_match = re.search(
        r"--- SCRIPT START ---\s*(.*?)\s*--- SCRIPT END ---",
        text,
        re.DOTALL
    )

    if not script_match:
        raise ValueError(
            f"Script boundaries not found in {path.name}"
        )

    script = script_match.group(1)

    # Identify scene boundaries.
    scene_matches = list(
        re.finditer(
            r"^SCENE\s+\d+\s*$",
            script,
            re.MULTILINE | re.IGNORECASE
        )
    )

    scenes = []

    for i, match in enumerate(scene_matches):

        start = match.start()

        end = (
            scene_matches[i + 1].start()
            if i + 1 < len(scene_matches)
            else len(script)
        )

        scene_text = script[start:end]

        scene = parse_scene(
            scene_text,
            metadata["episode_number"],
            warnings
        )

        if scene:
            scenes.append(scene)

    if not scenes:
        warnings.append("No scenes were detected.")

    return {
        "source_file": path.name,
        **metadata,
        "scenes": scenes,
        "warnings": warnings
    }


def save_episode_json(episode, output_dir):
    """Save parsed screenplay as JSON."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = (
        f"episode_{episode['episode_number']:03d}.json"
    )

    output_path = output_dir / filename

    output_path.write_text(
        json.dumps(episode, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return output_path


if __name__ == "__main__":

    input_dir = Path("data/raw")
    output_dir = Path("data/processed")

    files = sorted(input_dir.glob("*.txt"))

    print(f"Found {len(files)} screenplay files.\n")

    for file in files:

        try:
            episode = parse_screenplay(file)

            output_path = save_episode_json(
                episode, output_dir
            )

            event_count = sum(
                len(scene["events"])
                for scene in episode["scenes"]
            )

            print(
                f"Episode {episode['episode_number']}: "
                f"{len(episode['scenes'])} scenes, "
                f"{event_count} events"
            )

            print(f"Saved: {output_path}")

            if episode["warnings"]:
                print("Warnings:", episode["warnings"])

        except Exception as error:
            print(f"ERROR: {file.name}: {error}")
