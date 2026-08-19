"""
NPC偶遇剧情 文档→低代码 转换模块
放入 functions/ 目录，由 main.py 调用

输入格式：
第一行（可选）配置参数，如：
  @avatar=$123209657 @standing=$123208084 @plotid=13589919
后续按段落标题分隔：结识、闲聊低、闲聊高、送礼、表白、主动表白、劈腿低/高、复合低/高、分手
"""

import re


# ===================== 配置解析 =====================
def parse_config_line(first_line):
    """从第一行提取@key=value配置，返回(config_dict, is_config_line)"""
    config = {}
    if '@' in first_line:
        pairs = re.findall(r'@(\w+)=([^\s@]+)', first_line)
        if pairs:
            for k, v in pairs:
                config[k] = v
            return config, True
    return config, False


# ===================== 文档解析 =====================
def parse_document(text):
    lines = text.strip().split('\n')
    lines = [l.strip() for l in lines if l.strip()]

    section_keywords = [
        '结识', '闲聊低', '闲聊高', '闲聊', '送礼', '表白', '主动表白',
        '劈腿低', '劈腿高', '劈腿', '复合低', '复合高', '复合', '分手'
    ]

    npc_name = None
    for line in lines:
        m = re.match(r'【(.+?)】', line)
        if m and m.group(1) != '你':
            npc_name = m.group(1)
            break

    if not npc_name:
        raise ValueError("无法从文档中识别NPC名字，请确保有【NPC名】格式的对话")

    sections = {}
    current_section = None
    current_content = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        is_section = False
        for kw in section_keywords:
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
        if sec_name in ('闲聊低', '闲聊'):
            result['sections']['闲聊低'] = _parse_chat_section(content_lines)
        elif sec_name == '闲聊高':
            result['sections']['闲聊高'] = _parse_chat_section(content_lines)
        elif sec_name == '主动表白':
            result['sections']['主动表白'] = _parse_active_confession(content_lines)
        else:
            result['sections'][sec_name] = _parse_dialogue_lines(content_lines)

    return result


def _parse_dialogue_lines(lines):
    dialogues = []
    for line in lines:
        m = re.match(r'【(.+?)】(.+)', line)
        if m:
            dialogues.append((m.group(1), m.group(2).strip()))
    return dialogues


def _parse_chat_section(lines):
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


def _parse_active_confession(lines):
    result = {'opening': [], 'accept': [], 'reject': []}
    current_part = 'opening'
    for line in lines:
        stripped = line.strip()
        if re.match(r'^[AB][\.、．]?\s*', stripped):
            label = stripped[0]
            if label == 'A':
                current_part = 'accept'
                continue
            elif label == 'B':
                current_part = 'reject'
                continue
        if stripped in ('同意', '接受', '不同意', '拒绝'):
            current_part = 'accept' if stripped in ('同意', '接受') else 'reject'
            continue
        m = re.match(r'【(.+?)】(.+)', stripped)
        if m:
            result[current_part].append((m.group(1), m.group(2).strip()))
    return result


# ===================== 代码生成辅助 =====================
def _gen_dialog(role, content, npc_name):
    if role == '你':
        return (f'await ac.sysDialogOn({{roleName: `你`,'
                f'content: `{content}`,'
                f'id: 5494488,hasRoleName: true,hasBg: true,'
                f'hasRoleAvatar: true,roleAvatarResId: ac.var.立绘,}});')
    else:
        return (f'await ac.sysDialogOn({{roleName: `{role}`,'
                f'content: `{content}`,'
                f'id: 5603139,hasRoleName: true,hasBg: true,'
                f'hasRoleAvatar: false,}});')


def _gen_dialogues(dialogues, npc_name, indent='      '):
    lines = []
    for role, content in dialogues:
        lines.append(indent + _gen_dialog(role, content, npc_name))
    return '\n' + '\n'.join(lines)


# ===================== 主生成函数 =====================
def generate_code(data):
    npc_name = data['npc_name']
    sections = data['sections']

    meet_code = ''
    if '结识' in sections:
        meet_lines = []
        for role, content in sections['结识']:
            meet_lines.append('      ' + _gen_dialog(role, content, npc_name))
        meet_code = '\n'.join(meet_lines)

    chat_low = sections.get('闲聊低', [])
    chat_high = sections.get('闲聊高', [])
    total_low = len(chat_low)
    active_confession = sections.get('主动表白', {})

    code = f'''async function 偶遇{npc_name}() {{
  var npcName = '{npc_name}';
  let npcs = JSON.parse(ac.var.NPC);
  let npc = npcs[npcName];
  if(npc == undefined){{
    await 提示('不存在这个npc');
    return;
  }}
  await ac.createImage({{
    name: 'npc',
    index: 0,
    inlayer: 'window',
    resId: npc.立绘,
    pos: {{
      x: 640,
      y: 360,
    }},
    anchor: {{
      x: 50,
      y: 50,
    }},
    opacity: 100,
    scale: 80,
    visible: true,
    verticalFlip: false,
    horizontalFlip: false,
  }});
  function leave(){{
    if(npc.关系 != '暧昧'){{
      if(npc.关系 == '陌生'&& npc.好感 >= 50){{
        npc.关系 = '相识';
      }}else if(npc.关系 == '相识'&& npc.好感 >= 100){{
        npc.关系 = '朋友';
      }}else if(npc.关系 == '朋友'&& npc.好感 >= 200){{
        npc.关系 = '好友';
      }}else if(npc.关系 == '好友'&& npc.好感 >= 300){{
        npc.关系 = '暧昧';
      }}
    }}
    npcs[npcName].好感 = npc.好感;
    npcs[npcName].关系 = npc.关系;
    ac.var.NPC = JSON.stringify(npcs);
    ac.remove({{
      name: 'npc',
      effect: 'fadeout',
      duration: 300,
      canskip: true,
    }});
  }}'''

    code += '''
  if(npc.关系 == '陌生'){

    let ran = Math.floor(Math.random()*80);
    if(ac.var.咖位 * 10 + npc.好感 > ran){

'''
    if meet_code:
        code += '\n      \n' + meet_code + '\n'

    code += '''      await 结识npc(npcName);
      npc.关系 = '相识';
      await ac.sysDialogOff({
        effect: 'normal',
      });
    }

  }'''

    # ===== 闲聊 =====
    code += '''
  async function 闲聊() {
'''
    if total_low > 0:
        code += f'''
    let ran = await ac.random({{ min: 0, max: {total_low - 1}}});'''

    total_high = len(chat_high)
    if total_high > 0:
        total_all = total_low + total_high
        if active_confession and active_confession.get('opening'):
            total_all += 1
        code += f'''
    if(npc.好感>=100){{
      ran= await ac.random({{min:0,max:{total_all - 1}}})
    }}'''

    branch_index = 0
    for i, group in enumerate(chat_low):
        prefix = 'if' if i == 0 else '} else if'
        code += f'''
    {prefix} (ran === {i}) {{'''
        code += _gen_dialogues(group, npc_name)
        branch_index = i + 1

    if active_confession and active_confession.get('opening'):
        code += f'''

    }} else if (ran === {branch_index} && npc.好感>300 && npc.关系 =='暧昧') {{'''
        if active_confession.get('accept'):
            code += '''
      async function 接受() {'''
            code += _gen_dialogues(active_confession['accept'], npc_name, '        ')
            code += '''
        npc.关系 = '情人';
        await ac.sysDialogOn({
          roleName: `角色名`,
          content: `与${npc.名字}的关系已经达到"情人"。`,
          id: 5717510,
          hasRoleName: false,
          hasBg: true,
          hasRoleAvatar: false,
          roleAvatarResId: '$105355234',
        });

      }'''
        if active_confession.get('reject'):
            code += '''
      async function 拒绝() {'''
            code += _gen_dialogues(active_confession['reject'], npc_name, '        ')
            code += '''

      }'''

        code += _gen_dialogues(active_confession['opening'], npc_name)
        code += '''
await ac.createOptionGroup({
        name: 'textOptionGroup',
        defaultComposition: false,
        index: 0,
        inlayer: 'window',
        spacing: 60,
        anchor: { x: 50, y: 50 },
        clickAudio: { resId: '$104237531', vol: 80 },
        optionGroup: [
          { textContent: `接受`, nResId: '$104237186', sResId: '$104237185', x: 900, y: 300, clickFunc: 接受, },
          { textContent: `拒绝`, nResId: '$104237186', sResId: '$104237185', x: 900, y: 400, clickFunc: 拒绝, }
        ],
});'''
        branch_index += 1

    for i, group in enumerate(chat_high):
        ran_val = branch_index + i
        code += f'''

    }}else if(ran === {ran_val}){{'''
        code += _gen_dialogues(group, npc_name)

    code += '''

    }

    npc.好感 += 2;
    await ac.sysDialogOff({
      effect: 'normal',
    });
    ac.var.行动点 = ac.var.行动点 - 1;
    await money();
    await basicInfo();
    await leave();

  }'''

    # ===== 送礼 =====
    gift_dialogue = sections.get('送礼', [])
    gift_line = ''
    if gift_dialogue:
        gift_line = _gen_dialog(gift_dialogue[0][0], gift_dialogue[0][1], npc_name)

    code += f'''
  async function 送礼() {{

    await ac.callUI({{
      name: 'callUI24',
      uiId: 'rj4efojf',
    }});

    if(ac.var.赠送礼物 == ''){{

      ac.remove({{
        name: 'npc',
        effect: 'fadeout',
        duration: 300,
        canskip: true,
      }});
      return;
    }}



    {gift_line}
    
if(npc.喜好 !=undefined && ac.var.赠送礼物 == npc.喜好){{
      npc.好感 += 6;
      await ac.sysDialogOn({{
        roleName: `角色名`,
        content: `好感 + 6`,
        id: 5717510,
        hasRoleName: false,
        hasBg: true,
        hasRoleAvatar: false,
        roleAvatarResId: '$105355234',
      }});
    }}else{{
      npc.好感 += 3;
      await ac.sysDialogOn({{
        roleName: `角色名`,
        content: `好感 + 3`,
        id: 5717510,
        hasRoleName: false,
        hasBg: true,
        hasRoleAvatar: false,
        roleAvatarResId: '$105355234',
      }});
    }}await ac.sysDialogOff({{
      effect: 'normal',
    }});ac.var.行动点 = ac.var.行动点 - 1;
    await money();
    await basicInfo();
    await leave();

  }}'''

    # ===== 表白 =====
    confess = sections.get('表白', [])
    confess_low_cheat = sections.get('劈腿低', [])
    confess_high_cheat = sections.get('劈腿高', [])
    reconcile_low = sections.get('复合低', [])
    reconcile_high = sections.get('复合高', [])

    code += '''
  async function 表白() { '''

    if reconcile_low:
        code += '''
    if(npc.关系 == \'前任\' && npc.好感 <= 400) {

      npc.好感 -= 30;'''
        code += _gen_dialogues(reconcile_low, npc_name)
        code += '\n\n'

    if reconcile_high:
        code += '''
    } else if(npc.关系 == \'前任\' && npc.好感 > 400) {

'''
        code += _gen_dialogues(reconcile_high, npc_name)
        code += '''npc.关系 = '情人';
      await ac.sysDialogOn({
        roleName: `角色名`,
        content: `与${npc.名字}的关系已经达到"情人"。`,
        id: 5717510,
        hasRoleName: false,
        hasBg: true,
        hasRoleAvatar: false,
        roleAvatarResId: '$105355234',
      });

'''

    if confess_low_cheat:
        code += "    } else if(ac.var.官宣对象 != '' && ac.var.官宣对象 != npc.名字 && npc.好感 <= 400) {"
        code += _gen_dialogues(confess_low_cheat, npc_name)
        code += '\n\n'

    if confess_high_cheat:
        code += "    } else if(ac.var.官宣对象 != '' && ac.var.官宣对象 != npc.名字 && npc.好感 > 400) {\n\n"
        code += _gen_dialogues(confess_high_cheat, npc_name)
        code += """npc.关系 = '情人';
      await ac.sysDialogOn({
        roleName: `角色名`,
        content: `与${npc.名字}的关系已经达到"情人"。`,
        id: 5717510,
        hasRoleName: false,
        hasBg: true,
        hasRoleAvatar: false,
        roleAvatarResId: '$105355234',
      });

"""

    if confess:
        code += '''    } else {

      npc.关系 = '情人';'''
        code += _gen_dialogues(confess, npc_name)
        code += '''
      await ac.sysDialogOn({
        roleName: `角色名`,
        content: `与${npc.名字}的关系已经达到"情人"。`,
        id: 5717510,
        hasRoleName: false,
        hasBg: true,
        hasRoleAvatar: false,
        roleAvatarResId: '$105355234',
      });

    }'''

    code += '''
    await ac.sysDialogOff({
      effect: 'normal',
    });
    ac.var.行动点 = ac.var.行动点 - 1;
    await money();
    await basicInfo();
    await leave();
  }'''

    # ===== 分手 =====
    breakup = sections.get('分手', [])
    code += '''
  async function 分手() {

'''
    if breakup:
        code += _gen_dialogues(breakup, npc_name, '    ')

    code += '''await ac.sysDialogOff({
      effect: 'normal',
    });
    npc.好感 -= 300;
    npc.关系 = "前任"; 
    ac.var.行动点 = ac.var.行动点 - 1;
    await money();
    await basicInfo();
    await leave();

  }'''

    # ===== 官宣/离开/关系/信息/底部按钮（模板） =====
    code += '''
  async function 官宣() {

    await ac.sysDialogOn({
      roleName: `${npc.名字}`,
      content: `开发中`,
      id: 5494486,
      hasRoleName: false,
      hasBg: true,
      hasRoleAvatar: false,
      roleAvatarResId: '$1528927',
    });
    await ac.sysDialogOff({
      effect: 'normal',
    });
    npc.关系 = "情侣";
    ac.var.行动点 = ac.var.行动点 - 1;
    await money();
    await basicInfo();
    await leave();

  }
  async function 离开() {
    await leave();

  }
  async function 关系() {
    await ac.createOptionGroup({
      name: 'reactionGroup',
      defaultComposition: false,
      index: 0,
      inlayer: 'window',
      spacing: 80,
      anchor: {
        x: 50,
        y: 50,
      },
      clickAudio: {
        resId: '$104237531',
        vol: 80,
      },
      optionGroup: [{
        textContent: `表白`,
        nResId: '$104237186',
        sResId: '$104237185',
        x: 900,
        y: 400,
        clickFunc: 表白,
        condition: () => npc.关系 == '暧昧',
      }, {
        textContent: `官宣`,
        nResId: '$104237186',
        sResId: '$104237185',
        x: 900,
        y: 300,
        clickFunc: 官宣,
        condition: () => npc.关系 == '情人',
      }, {
        textContent: `分手`,
        nResId: '$104237186',
        sResId: '$104237185',
        x: 900,
        y: 200,
        clickFunc: 分手,
        condition: () => npc.关系 == '情人',
      }],
    });

  }
  async function 信息() {
    await ac.createImage({
      name: 'bottom',
      index: 0,
      inlayer: 'window',
      resId: '$127354360',
      pos: {
        x: 640,
        y: 360,
      },
      anchor: {
        x: 50,
        y: 50,
      },
      opacity: 100,
      scale: 100,
      visible: true,
      verticalFlip: false,
      horizontalFlip: false,
    });
    await ac.createStyle({
      name: 'stylenpc',
      font: '思源黑体',
      bold: false,
      italic: false,
      fontSize: 30,
      color: '#ffffff',
      speed: 10,
    });
    await ac.createText({
      name: 'text20',
      index: 0,
      inlayer: 'window',
      visible: true,
      content: `<tag style=stylenpc>姓名：${npc.名字}
性格：${npc.性格}
关系：${npc.关系}
好感：${npc.好感}
职业：${npc.类型}</tag>`,
      pos: {
        x: 640,
        y: 360,
      },
      size: {
        width: 400,
        height: 360,
      },
      direction: ac.TEXT_DIRECTION_TYPES.horizontal,
      halign: ac.HALIGN_TYPES.left,
      valign: ac.VALIGN_TYPES.center,
      spacing: 1.5,
      anchor: {
        x: 50,
        y: 50,
      },
    });
    async function 关闭信息() {
      ac.remove({
        name: 'bottom',
        effect: 'normal',
        canskip: false,
      });
      ac.remove({
        name: 'text20',
        effect: 'normal',
        canskip: false,
      });
      ac.remove({
        name: 'optionclose',
        effect: 'normal',
        canskip: false,
      });
      await ac.createOptionGroup({
        name: 'reactGroup',
        defaultComposition: false,
        index: 0,
        inlayer: 'window',
        spacing: 150,
        anchor: {
          x: 50,
          y: 50,
        },
        clickAudio: {
          resId: '$104237531',
          vol: 80,
        },
        optionGroup: [ {
          textContent: `闲聊`,
          nResId: '$107557464',
          sResId: '$107557465',
          x: 150,
          y: 100,
          clickFunc: 闲聊,
        },{
          textContent: `送礼`,
          nResId: '$107557464',
          sResId: '$107557465',
          x: 300,
          y: 100,
          clickFunc: 送礼,
        }, {
          textContent: `关系`,
          nResId: '$107557464',
          sResId: '$107557465',
          x: 450,
          y: 100,
          clickFunc: 关系,
          condition: () => npc.好感 >= 300,
        },{
          textContent: `信息`,
          nResId: '$107557464',
          sResId: '$107557465',
          x: 950,
          y: 100,
          clickFunc: 信息,
        }, {
          textContent: `离开`,
          nResId: '$107557464',
          sResId: '$107557465',
          x: 1100,
          y: 100,
          clickFunc: 离开,
        }],
      });

    }

    await ac.createOptionGroup({
      name: 'Optionclose',
      defaultComposition: false,
      index: 0,
      inlayer: 'window',
      spacing: 80,
      anchor: {
        x: 50,
        y: 50,
      },
      clickAudio: {
        resId: '$104237531',
        vol: 80,
      },
      optionGroup: [{
        textContent: ``,
        nResId: '$127354416',
        sResId: '$127354416',
        x: 640,
        y: 150,
        clickFunc: 关闭信息,
      }],
    });

  }
  await ac.createOptionGroup({
    name: 'reactGroup',
    defaultComposition: false,
    index: 0,
    inlayer: 'window',
    spacing: 150,
    anchor: {
      x: 50,
      y: 50,
    },
    clickAudio: {
      resId: '$104237531',
      vol: 80,
    },
    optionGroup: [ {
      textContent: `闲聊`,
      nResId: '$107557464',
      sResId: '$107557465',
      x: 150,
      y: 100,
      clickFunc: 闲聊,
    },{
      textContent: `送礼`,
      nResId: '$107557464',
      sResId: '$107557465',
      x: 300,
      y: 100,
      clickFunc: 送礼,
    }, {
      textContent: `关系`,
      nResId: '$107557464',
      sResId: '$107557465',
      x: 450,
      y: 100,
      clickFunc: 关系,
      condition: () => npc.好感 >= 300,
    },{
      textContent: `信息`,
      nResId: '$107557464',
      sResId: '$107557465',
      x: 950,
      y: 100,
      clickFunc: 信息,
    }, {
      textContent: `离开`,
      nResId: '$107557464',
      sResId: '$107557465',
      x: 1100,
      y: 100,
      clickFunc: 离开,
    }],
  });
}'''

    return code


# ===================== process 入口 =====================
def process(input_text):
    """main.py 调用的统一入口"""
    lines = input_text.strip().split('\n', 1)

    # 尝试解析第一行的配置（偶遇模块不需要avatar/standing，但保留扩展性）
    config, is_config = parse_config_line(lines[0])
    doc_text = lines[1] if is_config and len(lines) > 1 else input_text

    data = parse_document(doc_text)
    return generate_code(data)