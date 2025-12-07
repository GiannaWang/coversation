def process(text: str):
    """
    接收 main.py 输入区的文本，并返回转换后的内容。
    不再处理文件路径。
    """

    lines = [line.rstrip('\n') for line in text.split("\n")]

    code = []
    current_id = 0  # 遇到空行就重置

    for line in lines:
        # 空行：重置消息ID，不生成代码
        if not line.strip():
            current_id = 0
            continue

        # 识别发言者
        if line.startswith('【你】'):
            mode = 'ac.HALIGN_TYPES.right'
            bg_color = "'#7ed321'"
            roleAvatarResId = 'ac.var.头像'
            content = line[3:].strip()

        elif line.startswith('【npc】') or line.startswith('【NPC】'):
            mode = 'ac.HALIGN_TYPES.left'
            bg_color = "'#ffffff'"
            roleAvatarResId = 'npc.头像'
            content = line[5:].strip()

        else:
            # 不符合格式：跳过
            continue

        # 生成消息代码
        message_code = (
            f"await ac.createMessage({{\n"
            f"  chatId: 'chat', id: 'm{current_id}', mode: {mode},\n"
            f"  effect: ac.EFFECT_TYPES.moveinBottom, duration: 200,\n"
            f"  hasRoleName: false, roleName: ``, hasRoleAvatar: true, roleAvatarResId: {roleAvatarResId},\n"
            f"  type: ac.MESSAGE_TYPES.text, bgColor: {bg_color}, bgOpacity: 60,\n"
            f"  content: `<tag style=speak>{content}</tag>`,\n"
            f"  canBlock: true\n"
            f"}});"
        )

        code.append(message_code)
        current_id += 1

    return "\n\n".join(code)
