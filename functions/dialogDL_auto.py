import re
import os
from emotion_dict import detect_emotion
from portrait_dict import IMGS

imgs = IMGS

SPECIAL_PORTRAIT_VARS = {
    "助理": "ac.var.助理立绘",
    "经纪人": "ac.var.经纪人立绘",
}

def _normalize_emotion_tag(emotion_text):
    return detect_emotion(emotion_text)


def _resolve_image_name(role_name, emotion_text, use_ancient):
    suffix = _normalize_emotion_tag(emotion_text)
    base = f"{role_name}-" if use_ancient else role_name
    return f"{base}{suffix}" if suffix else base


def _has_future_speaker(parsed_lines, current_index, role_name, lookahead=5):
    end_index = min(len(parsed_lines), current_index + lookahead + 1)
    for i in range(current_index + 1, end_index):
        if parsed_lines[i].get("speaker") == role_name:
            return True
    return False


def process(input_text):
    output = []
    img_name_map = {item["名称"]: item["图片"] for item in imgs}
    length = 0
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

    use_ancient = False
    active_speakers = []
    slot_by_speaker = {}
    last_image_by_speaker = {}

    def _slot_name(role_name):
        if role_name not in slot_by_speaker:
            slot_by_speaker[role_name] = f"p{len(active_speakers) + 1}"
            active_speakers.append(role_name)
        return slot_by_speaker[role_name]

    def _forget_speaker(role_name):
        if role_name in slot_by_speaker:
            del slot_by_speaker[role_name]
        if role_name in last_image_by_speaker:
            del last_image_by_speaker[role_name]
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
        if "@古" in line:
            use_ancient = True
            line = line.replace("@古", "").strip()
            if not line:
                continue

        # 处理以 `/` 开头的选项
        if line.startswith("/"):
            # 提取/后的内容并按空格分割为选项（过滤空字符串）
            options = [opt for opt in line[1:].split() if opt]
            functions = []
            option_group = []

            for index, option in enumerate(options):
                # 直接使用选项内容作为函数名（移除可能的特殊字符确保合法性）
                func_name = ''.join([c for c in option if c.isalnum() or c == '_'])

                # 生成函数定义
                functions.append(f"async function {func_name}() {{\n\n}}")

                # 生成选项组配置（保持原有的位置计算逻辑）
                option_group.append(
                    f"{{ textContent: `{option}`, nResId: '$104237186', sResId: '$104237185', x: 900, y: {300 + index * 100}, clickFunc: {func_name}, }}"
                )

            # 更新length（记录已生成的函数总数）
            length += len(options)

            # 将生成的函数添加到输出
            output.extend(functions)

            # 生成 `await ac.createOptionGroup` 代码
            output.append("await ac.createOptionGroup({")
            output.append("  name: 'textOptionGroup',")
            output.append("  defaultComposition: false,")
            output.append("  index: 0,")
            output.append("  inlayer: 'window',")
            output.append("  spacing: 60,")
            output.append("  anchor: { x: 50, y: 50 },")
            output.append("  clickAudio: { resId: '$104237531', vol: 80 },")
            output.append("  optionGroup: [")
            output.append(",\n".join(option_group))
            output.append("  ],")
            output.append("});")

        # 处理对话（【角色】文本）
        elif line.startswith("【"):
            match = re.match(r'【(.*?)】(.*)', line)
            if match:
                role_name, content = match.groups()
                display_role_name = role_name
                display_content = content
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
                        emotion_text = content_emotion

                # 情况3：包含（你）和情绪词
                if "（你）" in role_name:
                    # 提取情绪，例如 sad / happy /shy /angry/close/peace/cry等
                    emotion_match = re.search(r'（你）(\w+)', role_name)
                    if emotion_match:
                        emotion = emotion_match.group(1)
                        output.append(
                            f"await ac.sysDialogOn({{roleName: `{display_role_name}`,content: `{display_content}`,id: 5494488,hasRoleName: true,hasBg: true,hasRoleAvatar: true,roleAvatarResId: currentCostume('{emotion}'),}});"
                        )
                    else:
                        # 如果没找到情绪，说明还是现代剧本
                        # 如果没找到情绪，说明还是现代剧本
                        output.append(
                            f"await ac.sysDialogOn({{roleName: `{display_role_name}`,content: `{display_content}`,id: 5494488,hasRoleName: true,hasBg: true,hasRoleAvatar: true,roleAvatarResId: ac.var.立绘,}});"
                        )

                # 情况1：刚好是“你”
                elif role_name.strip() == "你":
                    output.append(
                        f"await ac.sysDialogOn({{roleName: `{display_role_name}`,content: `{display_content}`,id: 5494488,hasRoleName: true,hasBg: true,hasRoleAvatar: true,roleAvatarResId: ac.var.立绘,}});"
                    )

                # 情况2：其他角色，无“你”
                else:
                    portrait_var = SPECIAL_PORTRAIT_VARS.get(role_name_clean)
                    image_name = role_name_clean if portrait_var else _resolve_image_name(role_name_clean, emotion_text, use_ancient)
                    res_id = portrait_var or img_name_map.get(image_name)
                    if res_id:
                        # ac.var 是 JS 表达式，资源 ID 才需要字符串引号。
                        res_id_expr = res_id if portrait_var else repr(res_id)
                        obj_name = slot_by_speaker.get(role_name_clean)
                        current_image = last_image_by_speaker.get(role_name_clean)
                        needs_new_image = current_image != image_name
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
                                f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: {res_id_expr},\n  pos: {{ x: {pos_x}, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: false,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});"
                            )
                            output.append(
                                f"ac.show({{\n  name: '{obj_name}',\n  effect: 'fadein',\n  duration: 300,\n  canskip: true,\n}});"
                            )
                        elif needs_new_image:
                            output.append(
                                f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: {res_id_expr},\n  pos: {{ x: {_speaker_pos(role_name_clean)}, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: true,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});"
                            )
                        if not obj_name or needs_new_image:
                            last_image_by_speaker[role_name_clean] = image_name
                        if len(active_speakers) >= 2:
                            for other in active_speakers:
                                other_obj = slot_by_speaker.get(other)
                                if other != role_name_clean and other_obj:
                                    _gray_speaker(other_obj)
                            _ungray_speaker(obj_name)
                    else:
                        output.append(f"// 未知角色图片：{image_name}")
                    output.append(
                        f"await ac.sysDialogOn({{roleName: `{display_role_name}`,content: `{display_content}`,id: 5603139,hasRoleName: true,hasBg: true,hasRoleAvatar: false,}});"
                    )
                    if not _has_future_speaker(parsed_lines, index, role_name_clean):
                        obj_name = slot_by_speaker.get(role_name_clean)
                        if obj_name:
                            output.append(
                                f"ac.remove({{\n  name: '{obj_name}',\n  effect: 'fadeout',\n  duration: 200,\n  canskip: true,\n}});"
                            )
                            _forget_speaker(role_name_clean)
        # 处理旁白条
        elif line.startswith("*"):
            content = line[1:] # 提取内容
            output.append(
                    f"await ac.sysDialogOn({{content: `{content}`,id: 5717510,hasRoleName: false,hasBg: true,hasRoleAvatar: false,}});")

        # 处理+动作指令
        elif line.startswith("+"):
            parts = line[1:].split()
            if len(parts) == 2:
                role, action = parts
                if role in img_name_map:
                    res_id = img_name_map[role]
                    index = next(i for i, x in enumerate(imgs) if x["名称"] == role)
                    obj_name = f"p{index // 4}"
                    if action == "消失":
                        if role in slot_by_speaker:
                            _forget_speaker(role)
                    if action == "出现":
                        output.append(
                            f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: '{res_id}',\n  pos: {{ x: 640, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: false,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});")
                        output.append(
                            f"ac.show({{\n  name: '{obj_name}',\n  effect: 'fadein',\n  duration: 300,\n  canskip: true,\n}});")
                    elif action == "消失":
                        output.append(
                            f"ac.remove({{\n  name: '{obj_name}',\n  effect: 'fadeout',\n  duration: 200,\n  canskip: true,\n}});")
                    elif action == "左移":
                        output.append(
                            f"ac.moveTo({{\n  name: '{obj_name}',\n  x: 340,\n  y: 360,\n  duration: 300,\n  ease: ac.EASE_TYPES.normal,\n  canskip: true,\n}});")
                    elif action == "右移":
                        output.append(
                            f"ac.moveTo({{\n  name: '{obj_name}',\n  x: 880,\n  y: 360,\n  duration: 300,\n  ease: ac.EASE_TYPES.normal,\n  canskip: true,\n}});")
                    elif action == "变灰":
                        output.append(
                            f"ac.changeMaskTo({{\n  name: '{obj_name}',\n  r: 74,\n  g: 74,\n  b: 74,\n  opacity: 50,\n  duration: 100,\n  canskip: true,\n}});")
                    elif action == "显示":
                        output.append(
                            f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: '{res_id}',\n  pos: {{ x: 640, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: true,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});")
                    elif action == "左边":
                        output.append(
                            f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: '{res_id}',\n  pos: {{ x: 340, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: true,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});")
                    elif action == "右边":
                        output.append(
                            f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: '{res_id}',\n  pos: {{ x: 880, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: true,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});")
                    elif action == "靠近":
                        output.append(
                            f"ac.scaleTo({{\n  name: '{obj_name}',\n  x: 100,\n  y: 100,\n  duration: 500,\n  ease: ac.EASE_TYPES.normal,\n  canskip: true,\n}});")
                    elif action == "远离":
                        output.append(
                            f"ac.scaleTo({{\n  name: '{obj_name}',\n  x: 70,\n  y: 70,\n  duration: 500,\n  ease: ac.EASE_TYPES.normal,\n  canskip: true,\n}});")
                    else:
                        output.append(f"// 未知动作：{action}")
                else:
                    output.append(f"// 未知角色：{role}")

        elif line.startswith("#"):
            content = line[1:] # 提取内容
            output.append(
                    f"{content}")

        # 处理普通旁白文本
        else:
            output.append(f"await ac.sysDialogOn({{roleName: `旁白`,content: `{line}`,id: 5494486,hasRoleName: false,hasBg: true,hasRoleAvatar: false,}});")

    return "\n".join(output)
