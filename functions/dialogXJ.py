import re
from emotion_dict import detect_emotion
from XJ_dict import IMGS

imgs = IMGS


def _resolve_image_name(role_name, emotion_text):
    suffix = detect_emotion(emotion_text)
    return f"{role_name}{suffix}" if suffix else role_name


def _has_future_speaker(parsed_lines, current_index, role_name, lookahead=5):
    end_index = min(len(parsed_lines), current_index + lookahead + 1)
    for i in range(current_index + 1, end_index):
        if parsed_lines[i].get("speaker") == role_name:
            return True
    return False


##仙界
def process(input_text):
    output = []
    img_name_map = {item["名称"]: item["图片"] for item in imgs}
    lines = input_text.splitlines()
    parsed_lines = []
    for raw in lines:
        line = raw.strip()
        entry = {"raw": raw, "line": line, "speaker": None, "emotion": None, "content": None}
        if line.startswith("【"):
            match = re.match(r'【(.*?)】(.*)', line)
            if match:
                role_name_raw, content = match.groups()
                emotion_match = re.search(r'（(.*?)）', role_name_raw)
                emotion = emotion_match.group(1) if emotion_match else None
                role_name_clean = role_name_raw
                if emotion:
                    role_name_clean = role_name_raw.replace(f"（{emotion}）", "")
                entry.update(
                    {
                        "speaker": role_name_clean.strip(),
                        "emotion": emotion,
                        "content": content,
                        "role_name_raw": role_name_raw,
                    }
                )
        parsed_lines.append(entry)

    active_speakers = []
    slot_by_speaker = {}

    def _slot_name(role_name):
        if role_name not in slot_by_speaker:
            slot_by_speaker[role_name] = f"p{len(active_speakers) + 1}"
            active_speakers.append(role_name)
        return slot_by_speaker[role_name]

    def _forget_speaker(role_name):
        if role_name in slot_by_speaker:
            del slot_by_speaker[role_name]
        if role_name in active_speakers:
            active_speakers.remove(role_name)

    def _gray_speaker(obj_name):
        output.append(
            f"ac.changeMaskTo({{\n  name: '{obj_name}',\n  r: 74,\n  g: 74,\n  b: 74,\n  opacity: 50,\n  duration: 1,\n  canskip: true,\n}});"
        )

    def _ungray_speaker(obj_name):
        output.append(
            f"ac.changeMaskTo({{\n  name: '{obj_name}',\n  r: 255,\n  g: 255,\n  b: 255,\n  opacity: 0,\n  duration: 1,\n  canskip: true,\n}});"
        )

    def _move_speaker(obj_name, x):
        output.append(
            f"ac.moveTo({{\n  name: '{obj_name}',\n  x: {x},\n  y: 360,\n  duration: 300,\n  ease: ac.EASE_TYPES.normal,\n  canskip: true,\n}});"
        )

    def _speaker_pos(role_name):
        if len(active_speakers) >= 2:
            if active_speakers[0] == role_name:
                return 340
            if active_speakers[1] == role_name:
                return 880
        return 640

    for index, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("【"):
            match = re.match(r'【(.*?)】(.*)', line)
            if match:
                role_name, content = match.groups()
                role_name_clean = role_name
                emotion_match = re.search(r'（(.*?)）', role_name)
                emotion_text = emotion_match.group(1) if emotion_match else None
                if emotion_text:
                    role_name_clean = role_name.replace(f"（{emotion_text}）", "")
                role_name_clean = role_name_clean.strip()
                if role_name_clean != "你" and "（你）" not in role_name:
                    content_match = re.match(r'^（(.*?)）\s*(.*)', content)
                    if content_match:
                        content_emotion = content_match.group(1)
                        content = content_match.group(2)
                        emotion_text = content_emotion

                if "你" in role_name:
                    output.append(
                        f"await ac.sysDialogOn({{roleName: `{role_name}`,content: `{content}`,id: 3260426,hasRoleName: true,hasBg: true,hasRoleAvatar: true,roleAvatarResId: p0,}});"
                    )
                else:
                    image_name = _resolve_image_name(role_name_clean, emotion_text)
                    res_id = img_name_map.get(image_name)
                    if res_id:
                        obj_name = slot_by_speaker.get(role_name_clean)
                        if not obj_name:
                            obj_name = _slot_name(role_name_clean)
                            pos_x = 640
                            if len(active_speakers) == 2:
                                other = active_speakers[0]
                                other_obj = slot_by_speaker.get(other)
                                if other_obj:
                                    _move_speaker(other_obj, 340)
                                    _gray_speaker(other_obj)
                                pos_x = 880
                            output.append(
                                f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: '{res_id}',\n  pos: {{ x: {pos_x}, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: false,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});"
                            )
                            output.append(
                                f"ac.show({{\n  name: '{obj_name}',\n  effect: 'fadein',\n  duration: 300,\n  canskip: true,\n}});"
                            )
                        else:
                            output.append(
                                f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: '{res_id}',\n  pos: {{ x: {_speaker_pos(role_name_clean)}, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: true,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});"
                            )
                        if len(active_speakers) >= 2:
                            for other in active_speakers:
                                other_obj = slot_by_speaker.get(other)
                                if other != role_name_clean and other_obj:
                                    _gray_speaker(other_obj)
                            _ungray_speaker(obj_name)
                    else:
                        output.append(f"// 未知角色图片：{image_name}")
                    output.append(
                        f"await ac.sysDialogOn({{roleName: `{role_name_clean}`,content: `{content}`,id: 2411524,hasRoleName: true,hasBg: true,hasRoleAvatar: false,}});"
                    )
                    if not _has_future_speaker(parsed_lines, index, role_name_clean):
                        obj_name = slot_by_speaker.get(role_name_clean)
                        if obj_name:
                            output.append(
                                f"ac.remove({{\n  name: '{obj_name}',\n  effect: 'fadeout',\n  duration: 200,\n  canskip: true,\n}});"
                            )
                            _forget_speaker(role_name_clean)
        else:
            output.append(
                f"await ac.sysDialogOn({{roleName: `旁白`,content: `{line}`,id: 2411532,hasRoleName: false,hasBg: true,hasRoleAvatar: false,}});"
            )

    return "\n".join(output)
