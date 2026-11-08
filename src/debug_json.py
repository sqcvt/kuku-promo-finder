import json
from pathlib import Path

file_path = Path(
    "data/processed/episode_001.json"
)

episode = json.loads(
    file_path.read_text(encoding="utf-8")
)

print("ROOT TYPE:", type(episode))
print("ROOT KEYS:", episode.keys() if isinstance(episode, dict) else None)

if isinstance(episode, dict):

    print("\nEPISODE NUMBER:", episode.get("episode_number"))

    scenes = episode.get("scenes")

    print("SCENES TYPE:", type(scenes))
    print("NUMBER OF SCENES:", len(scenes) if isinstance(scenes, list) else None)

    if scenes:
        scene = scenes[0]

        print("\nFIRST SCENE:")
        print(scene)

        if isinstance(scene, dict):

            events = scene.get("events")

            print("\nEVENTS TYPE:", type(events))

            if isinstance(events, list) and events:
                print("\nFIRST EVENT:")
                print(events[0])