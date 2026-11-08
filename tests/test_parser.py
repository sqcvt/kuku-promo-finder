
from pathlib import Path
import sys

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)

from src.parser import parse_screenplay


def test_episode_metadata():

    files = list(Path("data/raw").glob("*.txt"))

    assert files, "No screenplay files found."

    for file in files:

        episode = parse_screenplay(file)

        assert episode["episode_number"] > 0, (
            f"Invalid episode number: {file.name}"
        )

        assert len(episode["scenes"]) > 0, (
            f"No scenes found: {file.name}"
        )

        for scene in episode["scenes"]:

            assert scene["heading"], (
                f"Missing scene heading in {file.name}, "
                f"Scene {scene['scene_number']}"
            )

            assert scene["start_seconds"] is not None, (
                f"Missing scene start: {file.name}, "
                f"Scene {scene['scene_number']}"
            )

            assert scene["end_seconds"] is not None, (
                f"Missing scene end: {file.name}, "
                f"Scene {scene['scene_number']}"
            )

            for event in scene["events"]:

                assert event["start_seconds"] >= 0

                if event["end_seconds"] is not None:
                    assert (
                        event["end_seconds"]
                        >= event["start_seconds"]
                    )
