imgs = [{"名称":"左琳","图片":"$177639892"},{"名称":"赵欣","图片":"$177639890"},{"名称":"姚影","图片":"$177639888"},{"名称":"祁沐瑶","图片":"$177639884"},{"名称":"廖熙宁","图片":"$177639883"},{"名称":"姜念梨","图片":"$177639882"},{"名称":"贺颜","图片":"$177639881"},{"名称":"小高","图片":"$177639591"},{"名称":"司空辰","图片":"$177639590"},{"名称":"柯浔","图片":"$177639586"},{"名称":"康信","图片":"$177639584"},{"名称":"江砚","图片":"$177639580"},{"名称":"韩云峥","图片":"$177639579"},{"名称":"父亲千金","图片":"$177639558"},{"名称":"杜长河","图片":"$177639544"},{"名称":"楚铭阳","图片":"$177639530"},{"名称":"千金母亲","图片":"$150297142"},{"名称":"导师","图片":"$150297141"},{"名称":"容聿风","图片":"$124579550"},{"名称":"戚寻音","图片":"$124579549"},{"名称":"陆瓷","图片":"$12457948"},{"名称":"胡青山","图片":"$124579547"},{"名称":"徐子衿","图片":"$123209663"},{"名称":"盛成林","图片":"$123209662"},{"名称":"尚峋","图片":"$123209661"},{"名称":"孟怀栋","图片":"$123209660"},{"名称":"纪梓","图片":"$123209659"},{"名称":"侯晓航","图片":"$123209658"},{"名称":"何嘉骏","图片":"$123209657"},{"名称":"杜海波","图片":"$123209656"},{"名称":"Reid","图片":"$123209654"},{"名称":"章家树","图片":"$123131215"},{"名称":"王泽阳","图片":"$123131214"},{"名称":"女14","图片":"$123131213"},
         {"名称":"女13","图片":"$123131212"},{"名称":"女12","图片":"$123131211"},{"名称":"女11","图片":"$123131210"},{"名称":"女10","图片":"$123131209"},{"名称":"陈东宇","图片":"$123131208"},{"名称":"赵欣然","图片":"$123008720"},{"名称":"叶知棠","图片":"$123008719"},{"名称":"吴柚宁","图片":"$123008718"},{"名称":"陶秀荷","图片":"$123008717"},{"名称":"唐锦","图片":"$123008716"},{"名称":"秦曼莉","图片":"$123008715"},{"名称":"女9","图片":"$123008714"},{"名称":"梁玟率","图片":"$123008713"},{"名称":"江雨霏","图片":"$123008712"},{"名称":"傅梦梧","图片":"$123008711"},{"名称":"方婧","图片":"$123008710"},{"名称":"曹瑞洁","图片":"$123008709"},{"名称":"夜允浩","图片":"$121896444"},{"名称":"童欣","图片":"$121896443"},{"名称":"宋芙妮","图片":"$121896442"},{"名称":"女8","图片":"$121896441"},{"名称":"女7","图片":"$121896440"},{"名称":"女6","图片":"$121896439"},{"名称":"男9","图片":"$121896438"},{"名称":"男8","图片":"$121896437"},{"名称":"男7","图片":"$121896436"},{"名称":"男6","图片":"$121896435"},{"名称":"女5","图片":"$121724865"},{"名称":"女4","图片":"$121724864"},{"名称":"女3","图片":"$121724863"},{"名称":"女2","图片":"$121724862"},{"名称":"男5","图片":"$121724861"},{"名称":"男4","图片":"$121724860"},{"名称":"朱默","图片":"$121313835"},
         {"名称":"周亦年","图片":"$121313834"},{"名称":"陈星卉","图片":"$121313833"},{"名称":"郑安芽","图片":"$121313832"},{"名称":"尤紫璇","图片":"$121313831"},{"名称":"樊修玥","图片":"$121313830"},{"名称":"严永刚","图片":"$121313829"},{"名称":"徐宥诚","图片":"$121313828"},{"名称":"谢柏臣","图片":"$121313827"},{"名称":"宋昭野","图片":"$121313825"},{"名称":"时千勋","图片":"$121313824"},{"名称":"商月眠","图片":"$121313823"},{"名称":"秦意初","图片":"$121313822"},{"名称":"女1","图片":"$121313821"},{"名称":"男3","图片":"$121313820"},{"名称":"男2","图片":"$121313819"},{"名称":"罗书茵","图片":"$121313817"},{"名称":"路子烨","图片":"$121313815"},{"名称":"陆燃","图片":"$121313814"},{"名称":"柳在溪","图片":"$121313813"},{"名称":"厉北辰","图片":"$121313811"},{"名称":"孔令萱","图片":"$121313810"},{"名称":"蒋溯云","图片":"$121313809"},{"名称":"简若汐","图片":"$121313808"},{"名称":"季楚","图片":"$121313807"},{"名称":"霍凛川","图片":"$121313806"},{"名称":"薛牧之","图片":"$121313805"},{"名称":"陈榕","图片":"$121313804"},{"名称":"宋祈明","图片":"$193851785"},{"名称":"","图片":"$"},{"名称":"谷盈溪","图片":"$193851784"},{"名称":"叶疏桐","图片":"$177648760"},{"名称":"","图片":"$"}]

def process(text: str):
    # 安全构建映射，使用 .get() 容错，杜绝键不存在报错
    role_img_map = {}
    for idx, item in enumerate(imgs):
        # 用get防止字典缺失键
        name_raw = item.get("名称", "")
        pic_res = item.get("图片", "")
        clean_name = name_raw.strip()
        # 过滤空名字，不存入映射
        if clean_name:
            role_img_map[clean_name] = pic_res

    lines = [line.rstrip('\n') for line in text.split("\n")]

    code = [
        '''await ac.createLayer({name: 'layermain',index: 100,inlayer: 'window',visible: true,pos: {x: 640,y: 360,},anchor: {x: 50,y: 50,},size: {width: 1280,height: 720,},clipMode: false,});''',
        '''await ac.createImage({name: 'bottom',index: 0,inlayer: 'layermain',resId: '$181057131',pos: {x: 640,y: 330,},anchor: {x: 50,y: 50,},opacity: 100,scale: 100,visible: true,verticalFlip: false,horizontalFlip: false,});''',
        '''await ac.createStyle({name: 'stylename',font: '思源黑体',bold: false,italic: false,fontSize: 30,color: '#000000',speed: 10,});''',
        '''await ac.createStyle({name: 'speak',font: '思源黑体',bold: false,italic: false,fontSize: 30,color: '#000000',speed: 10,});''',
        '''await ac.createText({name: 'textname',index: 0,inlayer: 'layermain',visible: true,content: `<tag style=stylename>${npc.名字}</tag>`,pos: {x: 640,y: 550,},size: {width: 200,height: 50,},direction: ac.TEXT_DIRECTION_TYPES.horizontal,halign: ac.HALIGN_TYPES.middle,valign: ac.VALIGN_TYPES.center,spacing: 1,anchor: {x: 50,y: 50,},});''',
        '''await ac.createChat({name: 'chat0',index: 0,inlayer: 'layermain',visible: true,size: {width: 1100,height: 420,},anchor: {x: 50,y: 50,},pos: {x: 640,y: 310,},sort: ac.CHAT_SORT_TYPES.bottom,});''',
        '''await ac.createStyle({name: 'attention',font: '思源黑体',bold: false,italic: false,fontSize: 24,color: '#4a4a4a',speed: 10,});''',
        '''await ac.createImage({name: 'down',index: 0,inlayer: 'layermain',resId: '$181058275',pos: {x: 640,y: -25,},anchor: {x: 50,y: 50,},opacity: 100,scale: 100,visible: true,verticalFlip: false,horizontalFlip: false,});'''
    ]
    current_id = 0

    for line in lines:
        strip_line = line.strip()
        if not strip_line:
            current_id = 0
            continue

        mode = ""
        bg_color = ""
        roleAvatarResId = ""
        content = strip_line

        if strip_line.startswith('【你】'):
            mode = 'ac.HALIGN_TYPES.right'
            bg_color = "'#7ed321'"
            roleAvatarResId = 'ac.var.头像'
            content = strip_line[3:].strip()
        elif strip_line.startswith('【npc') or strip_line.startswith('【NPC'):
            mode = 'ac.HALIGN_TYPES.left'
            bg_color = "'#ffffff'"
            roleAvatarResId = "'$158612363'"
            content = strip_line[5:].strip()
        elif strip_line.startswith('【'):
            # 分割角色与内容，限制分割一次
            head_part, tail_part = strip_line.split('】', 1)
            role_name = head_part.replace('【', '').strip()
            content = tail_part.strip()
            mode = 'ac.HALIGN_TYPES.left'
            bg_color = "'#ffffff'"
            # 安全取值，不存在使用默认头像
            res = role_img_map.get(role_name, "$158612363")
            roleAvatarResId = f"'{res}'"
        else:
            mode = 'ac.HALIGN_TYPES.middle'
            bg_color = "'#ffffff'"
            roleAvatarResId = ''

        # f-string JS对象大括号全部双转义 {{ }}
        message_code = f'''await ac.createMessage({{
  chatId: 'chat0', id: 'm{current_id}', mode: {mode},
  effect: ac.EFFECT_TYPES.moveinBottom, duration: 200,
  hasRoleName: false, roleName: ``, hasRoleAvatar: true, roleAvatarResId: {roleAvatarResId},
  type: ac.MESSAGE_TYPES.text, bgColor: {bg_color}, bgOpacity: 60,
  content: `<tag style=speak>{content}</tag>`,
  canBlock: true
}});'''
        code.append(message_code)
        current_id += 1

    # 结尾清理仅生成一次
    code.append('''await ac.chatClear({name: 'chat0',});''')
    code.append('''ac.hide({name: 'layermain',effect: 'normal',canskip: false});''')

    return "\n\n".join(code)

# 测试入口
if __name__ == "__main__":
    test_text = """【秦意初】今天天气很好
【你】确实不错
旁白内容无括号
【NPC】随便说一句
"""
    output = process(test_text)
    print(output)
