"""
NPC网聊剧情 文档→低代码 转换模块
放入 functions/ 目录，由 main.py 调用

输入格式：
第一行必填配置参数：
  @avatar=$121313811 @standing=$120960882 @plotid=13589919
  - avatar: NPC聊天头像资源ID
  - standing: NPC立绘资源ID（约会剧情用）
  - plotid: 约会结束后跳转的剧情ID（默认13589919）

后续按段落标题分隔：
  网聊低/高、主动网聊低/高、约会剧情
"""

import re


# ===================== 配置解析 =====================
def parse_config_line(first_line):
    """从第一行提取@key=value配置"""
    config = {}
    if '@' in first_line:
        pairs = re.findall(r'@(\w+)=([^\s@]+)', first_line)
        if pairs:
            for k, v in pairs:
                config[k] = v
            return config, True
    return config, False


# ===================== 文档解析 =====================
def parse_chat_document(text):
    lines = text.strip().split('\n')
    lines = [l.strip() for l in lines if l.strip()]

    section_keywords = [
        '网聊低', '网聊高', '网聊',
        '主动网聊低', '主动网聊高', '主动',
        '约会剧情', '官宣',
    ]

    npc_name = None
    for line in lines:
        m = re.match(r'【(.+?)】', line)
        if m and m.group(1) != '你':
            npc_name = m.group(1)
            break

    if not npc_name:
        raise ValueError("无法从文档中识别NPC名字")

    sections = {}
    current_section = None
    current_content = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        is_section = False

        # "主动" section后面的"网聊低/高/网聊"要合并
        if not is_section and current_section == '主动' and stripped in ('网聊低', '网聊高', '网聊'):
            if current_content:
                sections[current_section] = current_content
            current_section = '主动' + stripped
            current_content = []
            is_section = True

        if not is_section and current_section == '主动网聊' and stripped in ('低', '高'):
            if current_content:
                sections[current_section] = current_content
            current_section = '主动网聊' + stripped
            current_content = []
            is_section = True

        if not is_section:
            for kw in sorted(section_keywords, key=len, reverse=True):
                if stripped == kw:
                    is_section = True
                    if current_section and current_content:
                        sections[current_section] = current_content
                    current_section = kw
                    current_content = []
                    break

        if not is_section and stripped in ('低', '高'):
            if current_section:
                if current_content:
                    sections[current_section] = current_content
                current_section = current_section + stripped
                current_content = []
                is_section = True

        if not is_section:
            current_content.append(stripped)

    if current_section and current_content:
        sections[current_section] = current_content

    result = {'npc_name': npc_name, 'sections': {}}

    for sec_name, content_lines in sections.items():
        if sec_name in ('网聊低', '网聊'):
            result['sections']['网聊低'] = _parse_chat_groups(content_lines)
        elif sec_name == '网聊高':
            result['sections']['网聊高'] = _parse_chat_groups(content_lines)
        elif sec_name in ('主动网聊低', '主动低'):
            result['sections']['主动网聊低'] = _parse_chat_groups(content_lines)
        elif sec_name in ('主动网聊高', '主动高'):
            result['sections']['主动网聊高'] = _parse_chat_groups(content_lines)
        elif sec_name == '约会剧情':
            result['sections']['约会剧情'] = _parse_date_section(content_lines)
        else:
            result['sections'][sec_name] = content_lines

    return result


def _parse_chat_groups(lines):
    groups = []
    current_group = []
    for line in lines:
        if re.match(r'^\d+[\.\、．]?\s*$', line):
            if current_group:
                groups.append(current_group)
            current_group = []
            continue
        m = re.match(r'【(.+?)】(.+)', line)
        if m:
            current_group.append((m.group(1), m.group(2).strip()))
    if current_group:
        groups.append(current_group)
    return groups


def _parse_date_section(lines):
    date_groups = []
    current_group = []
    for line in lines:
        if re.match(r'^\d+[\.\、．]?\s*$', line):
            if current_group:
                date_groups.append(current_group)
            current_group = []
            continue
        current_group.append(line)
    if current_group:
        date_groups.append(current_group)

    scenes = []
    for group_lines in date_groups:
        scene = {
            'invite_chat': [],
            'accept_chat': [],
            'reject_chat': [],
            'date_location': '',
            'date_dialogue': [],
            'has_options': False,
        }
        current_part = 'invite'

        for line in group_lines:
            stripped = line.strip()

            if re.match(r'^[AB][\.、．]\s*', stripped):
                label = stripped[0]
                if label == 'A':
                    current_part = 'accept'
                    scene['has_options'] = True
                    continue
                elif label == 'B':
                    current_part = 'reject'
                    continue
            if stripped in ('同意', '接受'):
                current_part = 'accept'
                scene['has_options'] = True
                continue
            if stripped in ('不同意', '拒绝'):
                current_part = 'reject'
                continue

            if stripped.startswith('·') or stripped.startswith('·'):
                scene['date_location'] = stripped.lstrip('·').strip()
                current_part = 'date'
                continue

            m = re.match(r'【(.+?)】(.+)', stripped)
            if m:
                role = m.group(1)
                content = m.group(2).strip()
                if current_part == 'invite':
                    scene['invite_chat'].append((role, content))
                elif current_part == 'accept':
                    scene['accept_chat'].append((role, content))
                elif current_part == 'reject':
                    scene['reject_chat'].append((role, content))
                elif current_part == 'date':
                    scene['date_dialogue'].append(('dialogue', role, content))
            else:
                if current_part == 'date':
                    scene['date_dialogue'].append(('narration', None, stripped))
                elif current_part == 'invite':
                    scene['invite_chat'].append(('旁白', stripped))

        scenes.append(scene)
    return scenes


# ===================== 代码生成辅助 =====================
def _gen_message(role, content, msg_id, npc_avatar):
    if role == '你':
        return f'''await ac.createMessage({{
  chatId: 'chat', id: '{msg_id}', mode: ac.HALIGN_TYPES.right,
  effect: ac.EFFECT_TYPES.moveinBottom, duration: 200,
  hasRoleName: false, roleName: ``, hasRoleAvatar: true, roleAvatarResId: ac.var.头像,
  type: ac.MESSAGE_TYPES.text, bgColor: '#7ed321', bgOpacity: 60,
  content: `<tag style=speak>{content}</tag>`,
  canBlock: true
}});'''
    else:
        return f'''await ac.createMessage({{
  chatId: 'chat', id: '{msg_id}', mode: ac.HALIGN_TYPES.left,
  effect: ac.EFFECT_TYPES.moveinBottom, duration: 200,
  hasRoleName: false, roleName: ``, hasRoleAvatar: true, roleAvatarResId: {npc_avatar},
  type: ac.MESSAGE_TYPES.text, bgColor: '#ffffff', bgOpacity: 60,
  content: `<tag style=speak>{content}</tag>`,
  canBlock: true
}});'''


def _gen_messages(dialogues, npc_avatar, start_id=0, indent=''):
    lines = []
    for i, (role, content) in enumerate(dialogues):
        lines.append(indent + _gen_message(role, content, f'm{start_id + i}', npc_avatar))
    return '\n'.join(lines)


def _gen_sysDialog(role, content, npc_name):
    if role == '你':
        return (f'await ac.sysDialogOn({{roleName: `你`,'
                f'content: `{content}`,'
                f'id: 5494488,hasRoleName: true,hasBg: true,'
                f'hasRoleAvatar: true,roleAvatarResId: ac.var.立绘,}});')
    elif role == '旁白':
        return (f'await ac.sysDialogOn({{roleName: `旁白`,'
                f'content: `{content}`,'
                f'id: 5494486,hasRoleName: false,hasBg: true,'
                f'hasRoleAvatar: false,}});')
    else:
        return (f'await ac.sysDialogOn({{roleName: `{role}`,'
                f'content: `{content}`,'
                f'id: 5603139,hasRoleName: true,hasBg: true,'
                f'hasRoleAvatar: false,}});')


# ===================== 主生成函数 =====================
def generate_chat_code(data, npc_avatar, npc_standing, date_plot_id):
    npc_name = data['npc_name']
    sections = data['sections']

    chat_low = sections.get('网聊低', [])
    chat_high = sections.get('网聊高', [])
    active_low = sections.get('主动网聊低', [])
    active_high = sections.get('主动网聊高', [])
    date_scenes = sections.get('约会剧情', [])

    # 收集主动消息触发文本
    active_messages = []
    for group in active_low:
        if group and group[0][0] != '你':
            active_messages.append(group[0][1])
    for group in active_high:
        if group and group[0][0] != '你':
            active_messages.append(group[0][1])
    for scene in date_scenes:
        if scene.get('has_options') and scene['invite_chat']:
            first = scene['invite_chat'][0]
            if first[0] != '你':
                active_messages.append(first[1])

    code = f'''var 周几 = '';
await ac.createImage({{
  name: 'background',
  index: 0,
  inlayer: 'window',
  resId: currentRoom(),
  pos: {{
    x: 640,
    y: 360,
  }},
  anchor: {{
    x: 50,
    y: 50,
  }},
  opacity: 100,
  visible: true,
  verticalFlip: false,
  horizontalFlip: false,
  dynaScale: 'cover',
}});
await 卡屏按钮();
let npcs = JSON.parse(ac.var.NPC || '{{}}');
const 星期 = ['周一','周二','周三','周四','周五','周六','周日']
await ac.createStyle({{
    name: 'stylename',
    font: '思源黑体',
    bold: false,
    italic: false,
    fontSize: 30,
    color: '#ffffff',
    speed: 10,
}});
await ac.createStyle({{
    name: 'speak',
    font: '思源黑体',
    bold: false,
    italic: false,
    fontSize: 30,
    color: '#000000',
    speed: 10,
}});
await ac.createStyle({{
    name: 'attention',
    font: '思源黑体',
    bold: false,
    italic: false,
    fontSize: 24,
    color: '#4a4a4a',
    speed: 10,
}});'''

    # ==================== 入口1 ====================
    code += '''
if (ac.var.聊天入口 === 1) {
  let npc = JSON.parse(ac.var.当前npc);
  let ran = 0;
  await ac.createLayer({
    name: 'layermain',
    index: 100,
    inlayer: 'window',
    visible: true,
    pos: { x: 640, y: 360 },
    anchor: { x: 50, y: 50 },
    size: { width: 1280, height: 720 },
    clipMode: false,
  });
  await ac.createImage({
    name: 'bottom', index: 0, inlayer: 'layermain',
    resId: '$181057131',
    pos: { x: 640, y: 330 },
    anchor: { x: 50, y: 50 },
    opacity: 100, scale: 100, visible: true,
    verticalFlip: false, horizontalFlip: false,
  });
  await ac.createStyle({
    name: 'stylename', font: '思源黑体', bold: false, italic: false,
    fontSize: 30, color: '#000000', speed: 10,
  });
  await ac.createText({
    name: 'textname', index: 0, inlayer: 'layermain', visible: true,
    content: `<tag style=stylename>${npc.名字}</tag>
`,
    pos: { x: 640, y: 550 },
    size: { width: 200, height: 50 },
    direction: ac.TEXT_DIRECTION_TYPES.horizontal,
    halign: ac.HALIGN_TYPES.middle,
    valign: ac.VALIGN_TYPES.center,
    spacing: 1,
    anchor: { x: 50, y: 50 },
  });
  await ac.createChat({
    name: 'chat', index: 0, inlayer: 'layermain', visible: true,
    size: { width: 1100, height: 440 },
    anchor: { x: 50, y: 50 },
    pos: { x: 640, y: 300 },
    sort: ac.CHAT_SORT_TYPES.bottom,
  });'''

    # 打招呼
    code += '''
  async function 打招呼() {

    
await ac.createImage({
    name: 'down', index: 0, inlayer: 'layermain',
    resId: '$181058275',
    pos: { x: 640, y: -25 },
    anchor: { x: 50, y: 50 },
    opacity: 100, scale: 100, visible: true,
    verticalFlip: false, horizontalFlip: false,
    });'''

    total_low = len(chat_low)
    total_high = len(chat_high)
    max_groups = max(total_low, total_high, 1)

    if max_groups > 1:
        code += f'''ran = await ac.random({{ min: 0, max: {max_groups - 1} }});'''

    code += '''if(npc.好感 <= 200){
'''
    if total_low <= 1 and chat_low:
        code += _gen_messages(chat_low[0], npc_avatar, 0, '')
    elif total_low > 1:
        for i, group in enumerate(chat_low):
            prefix = '      if' if i == 0 else '      } else if'
            code += f'\n{prefix} (ran === {i}) {{\n'
            code += _gen_messages(group, npc_avatar, 0, '')
        code += '\n      }\n'

    code += '''

}else {
'''
    if total_high <= 1 and chat_high:
        code += _gen_messages(chat_high[0], npc_avatar, 0, '')
    elif total_high > 1:
        for i, group in enumerate(chat_high):
            prefix = '      if' if i == 0 else '      } else if'
            code += f'\n{prefix} (ran === {i}) {{\n'
            code += _gen_messages(group, npc_avatar, 0, '')
        code += '\n      }\n'

    code += '''

}

}'''

    # 约会函数
    player_dates = [s for s in date_scenes if not s.get('has_options') and s['invite_chat']]
    code += '''
async function 约会() {
  
await ac.createImage({
    name: 'down', index: 0, inlayer: 'layermain',
    resId: '$181058275',
    pos: { x: 640, y: -25 },
    anchor: { x: 50, y: 50 },
    opacity: 100, scale: 100, visible: true,
    verticalFlip: false, horizontalFlip: false,
});'''

    if player_dates:
        code += _gen_messages(player_dates[0]['invite_chat'], npc_avatar, 0, '')

    code += f'''
  async function 主控邀请约会(index) {{
    周几 = 星期[index];
    ac.playAudio({{
      name: 'playAudio22', resId: '$104175947', vol: 80, effect: 'normal', loop: false,
    }});
    ac.arr.夜间行程单[index] = {date_plot_id};
    ac.arr.约会类型[index] = '主控邀请约会';
    ac.arr.约会对象[index] = npc.名字;
    await ac.createMessage({{
      chatId: 'chat', id: 'm101', mode: ac.HALIGN_TYPES.middle,
      effect: ac.EFFECT_TYPES.moveinBottom, duration: 200,
      hasRoleName: false, roleName: ``, hasRoleAvatar: false, roleAvatarResId: '$279446',
      type: ac.MESSAGE_TYPES.text, bgColor: '#ffffff', bgOpacity: 80,
      content: `<tag style=attention>与${{npc.名字}}的约会已经加入下${{星期[index]}}夜间行程</tag>`,
      canBlock: true,
    }});
  }}
  await ac.createOptionGroup({{
    name: 'chooseday', defaultComposition: false, index: 0, inlayer: 'layermain',
    spacing: 80, anchor: {{ x: 50, y: 50 }},
    clickAudio: {{ resId: '$104237531', vol: 80 }},
    optionGroup: [
      {{textContent:`周一`,nResId:'$125596708',sResId:'$125596707',x:1150,y:560,clickFunc:()=>主控邀请约会(0),condition:()=>ac.arr.夜间行程单[0]===0}},
      {{textContent:`周二`,nResId:'$125596708',sResId:'$125596707',x:1150,y:480,clickFunc:()=>主控邀请约会(1),condition:()=>ac.arr.夜间行程单[1]===0}},
      {{textContent:`周三`,nResId:'$125596708',sResId:'$125596707',x:1150,y:400,clickFunc:()=>主控邀请约会(2),condition:()=>ac.arr.夜间行程单[2]===0}},
      {{textContent:`周四`,nResId:'$125596708',sResId:'$125596707',x:1150,y:320,clickFunc:()=>主控邀请约会(3),condition:()=>ac.arr.夜间行程单[3]===0}},
      {{textContent:`周五`,nResId:'$125596708',sResId:'$125596707',x:1150,y:240,clickFunc:()=>主控邀请约会(4),condition:()=>ac.arr.夜间行程单[4]===0}},
      {{textContent:`周六`,nResId:'$125596708',sResId:'$125596707',x:1150,y:160,clickFunc:()=>主控邀请约会(5),condition:()=>ac.arr.夜间行程单[5]===0}},
      {{textContent:`周日`,nResId:'$125596708',sResId:'$125596707',x:1150,y:80,clickFunc:()=>主控邀请约会(6),condition:()=>ac.arr.夜间行程单[6]===0}},
    ],
  }});

}}'''

    # 底部按钮
    code += '''
await ac.createImage({
  name: 'down', index: 0, inlayer: 'layermain',
  resId: '$181058275',
  pos: { x: 640, y: 50 },
  anchor: { x: 50, y: 50 },
  opacity: 100, scale: 100, visible: true,
  verticalFlip: false, horizontalFlip: false,
});
await ac.createOptionGroup({
  name: 'textOptionGroup', defaultComposition: false, index: 0, inlayer: 'layermain',
  spacing: 80, anchor: { x: 50, y: 50 },
  clickAudio: { resId: '$104237531', vol: 80 },
  optionGroup: [{
    textContent: `打个招呼`,
    nResId: '$181058273', sResId: '$181058271',
    x: 350, y: 50, clickFunc: 打招呼,
  }, {
    textContent: `约会`,
    nResId: '$181058273', sResId: '$181058271',
    x: 920, y: 50, clickFunc: 约会,
    condition: npc.好感>=30,
  }],
});
  npcs[npc.名字].好感 += 1;
  await ac.createMessage({
    chatId: 'chat', id: 'm100', mode: ac.HALIGN_TYPES.middle,
    effect: ac.EFFECT_TYPES.moveinBottom, duration: 200,
    hasRoleName: false, roleName: ``, hasRoleAvatar: false, roleAvatarResId: '$279446',
    type: ac.MESSAGE_TYPES.text, bgColor: '#ffffff', bgOpacity: 60,
    content: `<tag style=attention>${npc.名字}好感+1</tag>`,
    canBlock: true,
  });
  await ac.chatClear({ name: 'chat' });
'''

    # ==================== 入口2 ====================
    code += '''
} else if (ac.var.聊天入口 === 2) {
  let npc = JSON.parse(ac.var.当前npc|| '{}');'''

    if active_messages:
        msg_list_str = json_dumps_like(active_messages)
        code += f'''
  const 消息 = {msg_list_str}'''

    code += '''
  await ac.createLayer({
    name: 'layermain', index: 100, inlayer: 'window', visible: true,
    pos: { x: 640, y: 360 }, anchor: { x: 50, y: 50 },
    size: { width: 1280, height: 720 }, clipMode: false,
  });
  await ac.createImage({
    name: 'bottom', index: 0, inlayer: 'layermain',
    resId: '$181057131',
    pos: { x: 640, y: 330 }, anchor: { x: 50, y: 50 },
    opacity: 100, scale: 100, visible: true,
    verticalFlip: false, horizontalFlip: false,
  });
  await ac.createStyle({
    name: 'stylename', font: '思源黑体', bold: false, italic: false,
    fontSize: 30, color: '#000000', speed: 10,
  });
  await ac.createText({
    name: 'textname', index: 0, inlayer: 'layermain', visible: true,
    content: `<tag style=stylename>${npc.名字}</tag>
`,
    pos: { x: 640, y: 550 },
    size: { width: 200, height: 50 },
    direction: ac.TEXT_DIRECTION_TYPES.horizontal,
    halign: ac.HALIGN_TYPES.middle,
    valign: ac.VALIGN_TYPES.center,
    spacing: 1, anchor: { x: 50, y: 50 },
  });
  await ac.createChat({
    name: 'chat', index: 0, inlayer: 'layermain', visible: true,
    size: { width: 1100, height: 440 },
    anchor: { x: 50, y: 50 },
    pos: { x: 640, y: 300 },
    sort: ac.CHAT_SORT_TYPES.bottom,
  });
  await ac.createImage({
    name: 'down', index: 0, inlayer: 'layermain',
    resId: '$181058275',
    pos: { x: 640, y: -25 }, anchor: { x: 50, y: 50 },
    opacity: 100, scale: 100, visible: true,
    verticalFlip: false, horizontalFlip: false,
  });'''

    msg_index = 0
    first_branch = True

    for group in active_low:
        if not group or group[0][0] == '你':
            continue
        prefix = 'if' if first_branch else '}else if'
        first_branch = False
        code += f'''
  {prefix}(npc.消息==消息[{msg_index}]){{
'''
        code += _gen_messages(group, npc_avatar, 1, '  ')
        code += '\n'
        msg_index += 1

    for group in active_high:
        if not group or group[0][0] == '你':
            continue
        prefix = 'if' if first_branch else '}else if'
        first_branch = False
        code += f'''
  {prefix}(npc.消息==消息[{msg_index}]){{
'''
        code += _gen_messages(group, npc_avatar, 1, '  ')
        code += '\n'
        msg_index += 1

    for scene in date_scenes:
        if scene.get('has_options') and scene['invite_chat']:
            first_msg = scene['invite_chat'][0]
            if first_msg[0] != '你':
                prefix = 'if' if first_branch else '}else if'
                first_branch = False
                code += f'''
  {prefix}(npc.消息==消息[{msg_index}]){{
'''
                code += _gen_messages(scene['invite_chat'], npc_avatar, 0, '  ')
                code += '\n'

                if scene['reject_chat']:
                    code += '    async function 拒绝() {\n'
                    code += _gen_messages(scene['reject_chat'], npc_avatar, 1, '      ')
                    code += '\n    }\n'

                date_type = scene.get('date_location', '约会')
                code += f'''
async function npc邀请约会(index) {{
  周几 = 星期[index];
  ac.playAudio({{ name: 'playAudio22', resId: '$104175947', vol: 80, effect: 'normal', loop: false }});
'''
                if scene['accept_chat']:
                    code += _gen_messages(scene['accept_chat'], npc_avatar, 1, '  ')
                    code += '\n'

                code += f'''  ac.arr.夜间行程单[index] = {date_plot_id};
  ac.arr.约会类型[index] = '{date_type}';
  ac.arr.约会对象[index] = npc.名字;
  await ac.createMessage({{
    chatId: 'chat', id: 'm101', mode: ac.HALIGN_TYPES.middle,
    effect: ac.EFFECT_TYPES.moveinBottom, duration: 200,
    hasRoleName: false, roleName: ``, hasRoleAvatar: false, roleAvatarResId: '$279446',
    type: ac.MESSAGE_TYPES.text, bgColor: '#ffffff', bgOpacity: 80,
    content: `<tag style=attention>与${{npc.名字}}的约会已经加入下${{星期[index]}}夜间行程</tag>`,
    canBlock: true,
  }});
}}
ac.createOptionGroup({{
  name:'chooseday', index:0, inlayer:'layermain', spacing:80,
  anchor:{{x:50,y:50}}, clickAudio:{{resId:'$104237531',vol:80}},
  optionGroup:[
    {{textContent:'周一',nResId:'$125596708',sResId:'$125596707',x:1100,y:640,clickFunc:function(){{npc邀请约会(0);}},condition:function(){{return ac.arr.夜间行程单[0]===0;}}}},
    {{textContent:'周二',nResId:'$125596708',sResId:'$125596707',x:1100,y:560,clickFunc:function(){{npc邀请约会(1);}},condition:function(){{return ac.arr.夜间行程单[1]===0;}}}},
    {{textContent:'周三',nResId:'$125596708',sResId:'$125596707',x:1100,y:480,clickFunc:function(){{npc邀请约会(2);}},condition:function(){{return ac.arr.夜间行程单[2]===0;}}}},
    {{textContent:'周四',nResId:'$125596708',sResId:'$125596707',x:1100,y:400,clickFunc:function(){{npc邀请约会(3);}},condition:function(){{return ac.arr.夜间行程单[3]===0;}}}},
    {{textContent:'周五',nResId:'$125596708',sResId:'$125596707',x:1100,y:320,clickFunc:function(){{npc邀请约会(4);}},condition:function(){{return ac.arr.夜间行程单[4]===0;}}}},
    {{textContent:'周六',nResId:'$125596708',sResId:'$125596707',x:1100,y:240,clickFunc:function(){{npc邀请约会(5);}},condition:function(){{return ac.arr.夜间行程单[5]===0;}}}},
    {{textContent:'周日',nResId:'$125596708',sResId:'$125596707',x:1100,y:160,clickFunc:function(){{npc邀请约会(6);}},condition:function(){{return ac.arr.夜间行程单[6]===0;}}}},
    {{textContent:'拒绝',nResId:'$125596708',sResId:'$125596707',x:1100,y:80,clickFunc:拒绝}}
  ]
}});
'''
                msg_index += 1

    if not first_branch:
        code += '}'

    code += '''
  npcs[npc.名字].好感 += 1;
  await ac.createMessage({
    chatId: 'chat', id: 'm100', mode: ac.HALIGN_TYPES.middle,
    effect: ac.EFFECT_TYPES.moveinBottom, duration: 200,
    hasRoleName: false, roleName: ``, hasRoleAvatar: false, roleAvatarResId: '$279446',
    type: ac.MESSAGE_TYPES.text, bgColor: '#ffffff', bgOpacity: 60,
    content: `<tag style=attention>${npc.名字}好感+1</tag>`,
    canBlock: true,
  });
  await ac.chatClear({ name: 'chat' });
'''

    # ==================== 入口3: 约会剧情 ====================
    code += '''
} else {
'''

    date_with_dialogue = [s for s in date_scenes if s['date_dialogue']]

    for i, scene in enumerate(date_with_dialogue):
        date_type = scene.get('date_location', f'约会{i+1}')
        if len(date_with_dialogue) > 1:
            prefix = 'if' if i == 0 else '}else if'
            if scene.get('has_options'):
                code += f"  {prefix}(ac.arr.约会类型[ac.var.weekday] == '{date_type}'){{\n"
            else:
                code += f"  {prefix}(true){{\n"

        code += f'''await ac.createImage({{
    name: 'b1', index: 0, inlayer: 'window',
    resId: '',//TODO: 填入{date_type}背景图资源ID
    pos: {{ x: 640, y: 360 }}, anchor: {{ x: 50, y: 50 }},
    opacity: 100, visible: true, verticalFlip: false, horizontalFlip: false, dynaScale: 'cover',
}});
await ac.createImage({{
  name: 'p18', index: 0, inlayer: 'window',
  resId: '{npc_standing}',
  pos: {{ x: 640, y: 360 }}, anchor: {{ x: 50, y: 50 }},
  opacity: 100, scale: ac.var.立绘大小, visible: false,
  verticalFlip: false, horizontalFlip: false,
}});
ac.show({{ name: 'p18', effect: 'fadein', duration: 300, canskip: true }});
'''
        for item in scene['date_dialogue']:
            if item[0] == 'dialogue':
                code += _gen_sysDialog(item[1], item[2], npc_name) + '\n'
            elif item[0] == 'narration':
                code += _gen_sysDialog('旁白', item[2], npc_name) + '\n'

        code += '''ac.remove({ name: 'p18', effect: 'fadeout', duration: 200, canskip: true });
'''

    if len(date_with_dialogue) > 1:
        code += '}\n'

    code += f'''
await ac.sysDialogOn({{
  roleName: `角色名`,
  content: ` {npc_name} 好感 + 5`,
  id: 5717510,
  hasRoleName: false, hasBg: true, hasRoleAvatar: false, roleAvatarResId: '$105355234',
}});
await ac.sysDialogOff({{ effect: 'normal' }});
npcs['{npc_name}'].好感 += 5;
ac.var.NPC = JSON.stringify(npcs);
ac.var.聊天入口 = 0;
ac.var.行动点 = ac.var.行动点 - 1;
ac.arr.夜间行程单[ac.var.weekday] = 0;
  await 时间跳转();
}}
ac.var.NPC = JSON.stringify(npcs);
ac.var.聊天入口 = 0;'''

    return code


def json_dumps_like(lst):
    """简易JSON数组序列化（不依赖json模块）"""
    items = []
    for s in lst:
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        items.append(f'"{escaped}"')
    return '[' + ','.join(items) + ']'


# ===================== process 入口 =====================
def process(input_text):
    """main.py 调用的统一入口"""
    lines = input_text.strip().split('\n', 1)

    config, is_config = parse_config_line(lines[0])
    if not is_config:
        raise ValueError(
            "网聊模块需要在第一行填写配置参数，格式：\n"
            "@avatar=$头像ID @standing=$立绘ID @plotid=剧情ID\n\n"
            "示例：\n"
            "@avatar=$121313811 @standing=$120960882 @plotid=13589919"
        )

    doc_text = lines[1] if len(lines) > 1 else ''
    if not doc_text.strip():
        raise ValueError("配置行之后没有文档内容")

    npc_avatar = "'" + config.get('avatar', '$158612363') + "'"
    npc_standing = config.get('standing', '$158612363')
    date_plot_id = int(config.get('plotid', '13589919'))

    data = parse_chat_document(doc_text)
    return generate_chat_code(data, npc_avatar, npc_standing, date_plot_id)