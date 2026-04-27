from utils.prompt_utils import build_scene_prompts, select_scene


def test_prompt_evolver_cumulative():
    scenes = build_scene_prompts(
        base_style="cinematic",
        base_negative="bad",
        scene_1="walks",
        scene_2="runs",
        inheritance_mode="cumulative",
    )
    assert len(scenes) == 2
    assert scenes[0]["positive"] == "cinematic, walks"
    assert scenes[1]["positive"] == "cinematic, walks, runs"
    assert select_scene(scenes, 2)["delta"] == "runs"


def test_prompt_evolver_replace():
    scenes = build_scene_prompts("style", "neg", "one", "two", inheritance_mode="replace")
    assert scenes[1]["positive"] == "style, two"
