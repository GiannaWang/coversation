import re
from emotion_dict import detect_emotion
from portrait_dict import IMGS

imgs = IMGS

# 标准化情绪标签
def _normalize_emotion_tag(emotion_text):
    if not emotion_text:
        return None
    return detect_emotion(emotion_text)

# NPC情绪英文转中文后缀
def _npc_emotion_suffix(emo_tag):
    if emo_tag == "smile":
        return "笑"
    elif emo_tag == "sad":
        return "悲"
    elif emo_tag == "angry":
        return "怒"
    # peace / cry 无后缀，使用基础人物图
    return None

# 【修复头部解析：兼容全角冒号，分割修复res未定义bug】
def _parse_header_mapping(all_lines):
    map_data = {
        "era": "现代",
        "you_name": "",
        "char_ref": {}  # key:剧本显示名(B)  value:图片资源前缀(A)
    }
    # 仅读取前5行头部
    head_lines = all_lines[:5]
    for line in head_lines:
        raw_strip = line.strip()
        if not raw_strip:
            continue
        # 匹配时代
        if raw_strip.startswith("时代："):
            map_data["era"] = raw_strip.replace("时代：", "").strip()
            continue
        # 匹配你
        if raw_strip.startswith("你："):
            map_data["you_name"] = raw_strip.replace("你：", "").strip()
            continue
        # 统一替换全角冒号为半角，再分割
        fixed_line = raw_strip.replace("：", ":")
        parts = [p.strip() for p in fixed_line.split(":", 2)]
        if len(parts) == 2:
            res_prefix, show_name = parts
            if res_prefix and show_name:
                map_data["char_ref"][show_name] = res_prefix
    return map_data

# 提取台词本区块
def _extract_script_block(lines):
    state = {
        "in_script": False,
        "desc": "",
        "dialog_lines_raw": []
    }
    for line in lines:
        raw_line = line
        sl = line.strip()
        if sl == "台词本：":
            state["in_script"] = True
            continue
        if state["in_script"]:
            if sl in ("演绎：", ""):
                break
            if sl.startswith("片段描述："):
                state["desc"] = sl.replace("片段描述：", "").strip()
            elif raw_line:
                state["dialog_lines_raw"].append(raw_line.rstrip("\n"))
    return state

# 提取演绎区块所有原始行
def _extract_perform_lines(lines):
    perform_lines = []
    in_perform = False
    for line in lines:
        raw_line = line.rstrip("\n")
        sl = line.strip()
        if sl == "演绎：":
            in_perform = True
            continue
        if in_perform and sl:
            perform_lines.append(raw_line)
    return perform_lines

# 拆分角色名与括号内情绪
def _split_role_emotion(raw_role):
    emo_match = re.search(r"（([^）]+)）", raw_role)
    if emo_match:
        emo = emo_match.group(1)
        clean_role = raw_role.replace(f"（{emo}）", "").strip()
        return clean_role, emo
    return raw_role.strip(), None

# 生成角色立绘文件名
def _build_img_name(res_prefix, emo_text, is_you=False):
    suffix_en = _normalize_emotion_tag(emo_text)
    if is_you:
        # 玩家你：英文情绪后缀
        if suffix_en:
            return f"{res_prefix}{suffix_en}"
        return res_prefix
    else:
        # NPC：中文情绪后缀
        suffix_cn = _npc_emotion_suffix(suffix_en)
        if suffix_cn:
            return f"{res_prefix}{suffix_cn}"
        return res_prefix

# 获取资源ID映射
def _get_img_resid(img_name):
    name_map = {item["名称"]: item["图片"] for item in imgs}
    return name_map.get(img_name)

# 向后5行检索是否存在同角色台词
def _has_next_speaker(line_list, curr_idx, target_res_prefix, char_ref):
    max_check = min(len(line_list), curr_idx + 6)
    for i in range(curr_idx + 1, max_check):
        l = line_list[i].strip()
        if l.startswith("【"):
            match_line = re.match(r"【(.*?)】", l)
            if not match_line:
                continue
            raw_r = match_line.group(1)
            r_clean, _ = _split_role_emotion(raw_r)
            curr_res = char_ref.get(r_clean, None)
            if curr_res == target_res_prefix:
                return True
    return False

# 处理//选项行
def _parse_option_line(line):
    raw = line.lstrip("//").strip()
    opt_raw_list = raw.split()
    opt_list = []
    for opt in opt_raw_list:
        is_correct = False
        opt_text = opt
        if opt.endswith("√"):
            is_correct = True
            opt_text = opt[:-1]
        opt_list.append({"text": opt_text, "correct": is_correct})
    return opt_list

def process(input_text):
    output = []
    raw_all_lines = input_text.splitlines()
    # 仅前5行读取头部定义
    header_map = _parse_header_mapping(raw_all_lines)
    era = header_map["era"]
    you_real_name = header_map["you_name"]
    char_ref = header_map["char_ref"]
    # 台词本、演绎区块解析
    script_block = _extract_script_block(raw_all_lines)
    script_desc = script_block["desc"]
    script_raw_dialogs = script_block["dialog_lines_raw"]
    perform_lines = _extract_perform_lines(raw_all_lines)
    # 缓存key统一使用图片资源前缀
    slot_map = {}
    active_roles = []
    last_draw_img = {}

    def get_slot(res_prefix):
        if res_prefix not in slot_map:
            slot_map[res_prefix] = f"p{len(active_roles)+1}"
            active_roles.append(res_prefix)
        return slot_map[res_prefix]

    def clear_role_cache(res_prefix):
        if res_prefix in slot_map:
            del slot_map[res_prefix]
        if res_prefix in last_draw_img:
            del last_draw_img[res_prefix]
        if res_prefix in active_roles:
            active_roles.remove(res_prefix)

    def gray_speaker(obj_name):
        output.append(f'''ac.changeMaskTo({{
  name: '{obj_name}',
  r: 74, g: 74, b: 74, opacity: 50, duration: 1, canskip: true
}});''')
    def ungray_speaker(obj_name):
        output.append(f'''ac.changeMaskTo({{
  name: '{obj_name}',
  r: 255, g: 255, opacity: 0, duration: 1, canskip: true
}});''')
    def move_speaker(obj_name, x):
        output.append(f'''ac.moveTo({{
  name: '{obj_name}', x: {x}, y: 360, duration: 300, ease: ac.EASE_TYPES.normal, canskip: true
}});''')
    def get_role_x(res_prefix):
        if len(active_roles) >= 2:
            if active_roles[0] == res_prefix:
                return 340
            if active_roles[1] == res_prefix:
                return 880
        return 640

    # 片段描述
    if script_desc:
        output.append(f'''await ac.sysDialogOn({{
  roleName: '',
  content: `（情景：{script_desc}）`,
  id: 5717510,
  hasRoleName: false,
  hasBg: true,
  hasRoleAvatar: false,
  roleAvatarResId: '$105355234',
}});''')
        output.append("await ac.sysDialogOff({ effect: 'normal', });")

    # 台词本 Opera 弹窗
    if script_raw_dialogs:
        line_count = len(script_raw_dialogs)
        total_inner_h = line_count * 30
        tag_blocks = []
        for raw_line in script_raw_dialogs:
            strip_l = raw_line.strip()
            is_you_line = strip_l.startswith(f"{you_real_name}：")
            if is_you_line:
                tag_blocks.append(f"<tag style=high>{raw_line}</tag>")
            else:
                tag_blocks.append(f"<tag style=opera>{raw_line}</tag>")
        full_opera_content = "\n".join(tag_blocks)
        output.append('''await ac.createImage({
  name: 'operabottom',
  index: 100,
  inlayer: 'window',
  resId: '$180741631',
  pos: { x: 640, y: 320, },
  anchor: { x: 50, y: 50, },
  opacity: 100, scale: 100, visible: true, verticalFlip: false, horizontalFlip: false,
});''')
        output.append(f'''await ac.createScrollView({{
  name: 'scrollView',
  index: 100,
  inlayer: 'window',
  visible: true,
  pos: {{ x: 640, y: 280, }},
  anchor: {{ x: 50, y: 50, }},
  size: {{ width: 1000, height: 520, }},
  innerSize: {{ width: 1000, height: {total_inner_h}, }},
  horizontalScroll: false, verticalScroll: true,
}});''')
        output.append(f'''await ac.createText({{
  name: 'textopera',
  index: 0,
  inlayer: 'scrollView',
  visible: true,
  content: `{full_opera_content}`,
  pos: {{ x: 500, y: {total_inner_h}, }},
  size: {{ width: 1000, height: {total_inner_h} }},
  direction: ac.TEXT_DIRECTION_TYPES.horizontal,
  halign: ac.HALIGN_TYPES.left,
  valign: ac.VALIGN_TYPES.top,
  spacing: 1.2,
  anchor: {{ x: 50, y: 100, }}
}});''')
        output.append('''async function opera() {
  ac.remove({ name: 'operabottom', effect: 'normal', canskip: false });
  ac.remove({ name: 'texttitle', effect: 'normal', canskip: false });
  ac.remove({ name: 'scrollView', effect: 'normal', canskip: false });
  ac.remove({ name: 'textopera', effect: 'normal' });
}''')
        output.append('''await ac.createOptionGroup({
  name: 'closeopera',
  defaultComposition: false,
  index: 100,
  inlayer: 'window',
  spacing: 80,
  anchor: { x: 50, y: 50 },
  clickAudio: { resId: '$104237531', vol: 80 },
  optionGroup: [{textContent: ``,nResId:'$180741634',sResId:'$180741634',x:1150,y:560,clickFunc:opera,}]
});''')

    # 演绎逐行处理
    for idx, line in enumerate(perform_lines):
        sl = line.strip()
        # // 选项分支
        if sl.startswith("//"):
            opt_list = _parse_option_line(sl)
            func_defs = []
            opt_group_items = []
            base_y = 300
            for opt_idx, opt in enumerate(opt_list):
                opt_text = opt["text"]
                func_name = re.sub(r'[^\w\u4e00-\u9fa5]', '', opt_text)
                y_pos = base_y + opt_idx * 100
                if opt["correct"]:
                    func_code = f'''async function {func_name}() {{
  await ac.sysDialogOn({{
    content: `（进度 + 3%）`,
    id: 5717510,
    hasRoleName: false,
    hasBg: true,
    hasRoleAvatar: false,
  }});
  increase = increase +3;
}}'''
                else:
                    func_code = f'''async function {func_name}() {{
  await ac.sysDialogOn({{
    roleName: `{you_real_name}`,
    content: `（经导演提醒后重新演绎 进度 - 3%）`,
    id: 5717510,
    hasRoleName: false,
    hasBg: true,
    hasRoleAvatar: false,
    roleAvatarResId: '$105355234',
  }});
  increase = increase -3;
}}'''
                func_defs.append(func_code)
                opt_item = f'''{{
    textContent: `{opt_text}`,
    nResId: '$104237186',
    sResId: '$104237185',
    x: 900,
    y: {y_pos},
    clickFunc: {func_name},
  }}'''
                opt_group_items.append(opt_item)
            output.extend(func_defs)
            output.append("await ac.createOptionGroup({")
            output.append("  name: 'textOptionGroup',")
            output.append("  defaultComposition: false,")
            output.append("  index: 0,")
            output.append("  inlayer: 'window',")
            output.append("  spacing: 60,")
            output.append("  anchor: { x: 50, y: 50 },")
            output.append("  clickAudio: { resId: '$104237531', vol: 80 },")
            output.append("  optionGroup: [")
            output.append(",\n".join(opt_group_items))
            output.append("  ],")
            output.append("});")
            continue
        # 纯旁白
        if not sl.startswith("【"):
            output.append(f'''await ac.sysDialogOn({{
  roleName: `旁白`,
  content: `{sl}`,
  id: 5494486,
  hasRoleName: false,
  hasBg: true,
  hasRoleAvatar: false,
}});''')
            continue
        # 修复：先定义match_line再使用
        match_line = re.match(r'【(.*?)】(.*)', sl)
        if not match_line:
            continue
        role_raw, talk_content = match_line.groups()
        display_role = role_raw
        display_text = talk_content
        role_clean, emotion_text = _split_role_emotion(role_raw)
        role_clean = role_clean.strip()
        # 台词内情绪覆盖
        if role_clean != "你" and "（你）" not in role_raw:
            content_match = re.match(r'^（(.*?)）\s*(.*)', talk_content)
            if content_match:
                emotion_text = content_match.group(1)
        # 玩家你分支
        if "（你）" in role_raw or role_clean == "你":
            emo_tag = emotion_text or "peace"
            if era == "古代":
                avatar_src = f"currentCostume('{emo_tag}', 0)"
            elif era == "民国":
                avatar_src = f"currentCostume('{emo_tag}', 1)"
            else:
                avatar_src = "ac.var.立绘"
            output.append(f'''await ac.sysDialogOn({{
  roleName: `{display_role}`,
  content: `{display_text}`,
  id: 5494488,
  hasRoleName: true,
  hasBg: true,
  hasRoleAvatar: true,
  roleAvatarResId: {avatar_src},
}});''')
            continue
        # NPC角色分支
        res_prefix = char_ref.get(role_clean, None)
        if not res_prefix:
            output.append(f"// 警告：剧本角色「{role_clean}」未匹配头部映射")
            output.append(f'''await ac.sysDialogOn({{
  roleName: `{display_role}`,
  content: `{display_text}`,
  id: 5603139,
  hasRoleName: true,
  hasBg: true,
  hasRoleAvatar: false,
}});''')
            continue
        img_name = _build_img_name(res_prefix, emotion_text, is_you=False)
        res_id = _get_img_resid(img_name)
        if res_id:
            obj = slot_map.get(res_prefix)
            need_refresh = last_draw_img.get(res_prefix, "") != img_name
            if not obj or need_refresh:
                obj = get_slot(res_prefix)
                pos_x = get_role_x(res_prefix)
                if len(active_roles) == 2 and active_roles[0] != res_prefix:
                    other_res = active_roles[0]
                    other_obj = slot_map[other_res]
                    move_speaker(other_obj, 340)
                    gray_speaker(other_obj)
                output.append(f'''await ac.createImage({{
  name: '{obj}',
  index: 0,
  inlayer: 'window',
  resId: '{res_id}',
  pos: {{ x: {pos_x}, y: 360 }},
  anchor: {{ x: 50, y: 50 }},
  opacity: 100,
  scale: ac.var.立绘大小,
  visible: true,
  verticalFlip: false,
  horizontalFlip: false,
}});''')
                if not slot_map.get(res_prefix):
                    output.append(f'''ac.show({{
  name: '{obj}', effect: 'fadein', duration: 300, canskip: true
}});''')
                last_draw_img[res_prefix] = img_name
            if len(active_roles) >= 2:
                for other_res in active_roles:
                    if other_res != res_prefix:
                        gray_speaker(slot_map[other_res])
                ungray_speaker(obj)
        else:
            output.append(f"// 缺失贴图：{img_name} 资源前缀：{res_prefix}")
        output.append(f'''await ac.sysDialogOn({{
  roleName: `{display_role}`,
  content: `{display_text}`,
  id: 5603139,
  hasRoleName: true,
  hasBg: true,
  hasRoleAvatar: false,
}});''')
        if not _has_next_speaker(perform_lines, idx, res_prefix, char_ref):
            obj = slot_map.get(res_prefix)
            if obj:
                output.append(f'''ac.remove({{
  name: '{obj}', effect: 'fadeout', duration: 200, canskip: true
}});''')
                clear_role_cache(res_prefix)

    return "\n".join(output)

# 测试入口
if __name__ == "__main__":
    test_input = """时代：古代
你：沈青瓷
秦意初：姬韫瑛
柯浔：拓跋烈
情景一：
台词本：
片段描述：两人庭院闲谈
场景：落樱庭院
姬韫瑛：今日风光甚好。
拓跋烈：确实很美。
演绎：
【姬韫瑛（smile）】今日风光甚好。
【拓跋烈（sad）】确实很美。
"""
    print(process(test_input))