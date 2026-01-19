import re
import os
from portrait_dict import IMGS

imgs = IMGS

def process(input_text):
    output = []
    img_name_map = {item["名称"]: item["图片"] for item in imgs}
    length = 0
    lines = input_text.splitlines()
    for line in lines:
        line = line.strip()

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
            match = re.match(r'【(.*?)】(.*)', line)
            if match:
                role_name, content = match.groups()

                # 情况3：包含（你）和情绪词
                if "（你）" in role_name:
                    # 提取情绪，例如 sad / happy /shy /angry/close/peace/cry等
                    emotion_match = re.search(r'（你）(\w+)', role_name)
                    if emotion_match:
                        emotion = emotion_match.group(1)
                        role_name_cleaned = role_name.replace(emotion, "")  # 去掉情绪
                        output.append(
                            f"await ac.sysDialogOn({{roleName: `{role_name_cleaned}`,content: `{content}`,id: 5494488,hasRoleName: true,hasBg: true,hasRoleAvatar: true,roleAvatarResId: currentCostume('{emotion}'),}});"
                        )
                    else:
                        # 如果没找到情绪，说明还是现代剧本
                        # 如果没找到情绪，说明还是现代剧本
                        output.append(
                            f"await ac.sysDialogOn({{roleName: `{role_name}`,content: `{content}`,id: 5494488,hasRoleName: true,hasBg: true,hasRoleAvatar: true,roleAvatarResId: ac.var.立绘,}});"
                        )

                # 情况1：刚好是“你”
                elif role_name.strip() == "你":
                    output.append(
                        f"await ac.sysDialogOn({{roleName: `{role_name}`,content: `{content}`,id: 5494488,hasRoleName: true,hasBg: true,hasRoleAvatar: true,roleAvatarResId: ac.var.立绘,}});"
                    )

                # 情况2：其他角色，无“你”
                else:
                    output.append(
                        f"await ac.sysDialogOn({{roleName: `{role_name}`,content: `{content}`,id: 5603139,hasRoleName: true,hasBg: true,hasRoleAvatar: false,}});"
                    )
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
                            f"ac.moveTo({{\n  name: '{obj_name}',\n  x: 300,\n  y: 360,\n  duration: 300,\n  ease: ac.EASE_TYPES.normal,\n  canskip: true,\n}});")
                    elif action == "右移":
                        output.append(
                            f"ac.moveTo({{\n  name: '{obj_name}',\n  x: 900,\n  y: 360,\n  duration: 300,\n  ease: ac.EASE_TYPES.normal,\n  canskip: true,\n}});")
                    elif action == "变灰":
                        output.append(
                            f"ac.changeMaskTo({{\n  name: '{obj_name}',\n  r: 74,\n  g: 74,\n  b: 74,\n  opacity: 50,\n  duration: 100,\n  canskip: true,\n}});")
                    elif action == "显示":
                        output.append(
                            f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: '{res_id}',\n  pos: {{ x: 640, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: true,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});")
                    elif action == "左边":
                        output.append(
                            f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: '{res_id}',\n  pos: {{ x: 300, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: true,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});")
                    elif action == "右边":
                        output.append(
                            f"await ac.createImage({{\n  name: '{obj_name}',\n  index: 0,\n  inlayer: 'window',\n  resId: '{res_id}',\n  pos: {{ x: 900, y: 360 }},\n  anchor: {{ x: 50, y: 50 }},\n  opacity: 100,\n  scale: ac.var.立绘大小,\n  visible: true,\n  verticalFlip: false,\n  horizontalFlip: false,\n}});")
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
