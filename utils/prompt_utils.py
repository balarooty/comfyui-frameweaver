def _clean(parts):
    return [part.strip() for part in parts if isinstance(part, str) and part.strip()]


def join_prompt(*parts: str) -> str:
    return ", ".join(_clean(parts))


def build_scene_prompts(
    base_style: str,
    base_negative: str,
    scene_1: str,
    scene_2: str = "",
    scene_3: str = "",
    scene_4: str = "",
    scene_5: str = "",
    bridge_1_to_2: str = "",
    bridge_2_to_3: str = "",
    bridge_3_to_4: str = "",
    bridge_4_to_5: str = "",
    inheritance_mode: str = "cumulative",
) -> list[dict]:
    scene_inputs = [scene_1, scene_2, scene_3, scene_4, scene_5]
    bridge_inputs = ["", bridge_1_to_2, bridge_2_to_3, bridge_3_to_4, bridge_4_to_5]
    scenes = []
    inherited = ""

    for index, scene_text in enumerate(scene_inputs, start=1):
        scene_text = (scene_text or "").strip()
        if not scene_text:
            continue
        if inheritance_mode == "replace" or not inherited:
            inherited = scene_text
        elif inheritance_mode == "blend":
            inherited = join_prompt(inherited, f"then transition toward: {scene_text}")
        else:
            inherited = join_prompt(inherited, scene_text)

        scenes.append(
            {
                "index": index,
                "positive": join_prompt(base_style, inherited),
                "negative": base_negative.strip(),
                "bridge": bridge_inputs[index - 1].strip(),
                "delta": scene_text,
            }
        )
    return scenes


def select_scene(prompt_list: list[dict], scene_index: int) -> dict:
    if not prompt_list:
        return {"index": 1, "positive": "", "negative": "", "bridge": "", "delta": ""}
    wanted = int(scene_index)
    for scene in prompt_list:
        if int(scene.get("index", 0)) == wanted:
            return scene
    return prompt_list[max(0, min(len(prompt_list) - 1, wanted - 1))]
