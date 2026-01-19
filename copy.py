# -*- coding: utf-8 -*-
import shutil
import os

# 文件来源目录
source_folder = 'G:\\作品\\许我万分闪耀\\npc\\导出png'
# 文件复制到的目标目录
target_folder = 'G:\\作品\\许我万分闪耀\\npc\\导出png'

# 创建目标目录（如果没有）
os.makedirs(target_folder, exist_ok=True)

# 你的名字数组
names = ["卫如歌","傅梦梧","张静珠","钱麟",]

# 源图片名字（放在 source_images 文件夹下）
sources = ["npc现.png", "npc古.png"]

# 表情后缀
suffixes = ["", "悲", "怒", "笑"]

for name in names:
    for src in sources:
        src_path = os.path.join(source_folder, src)

        if not os.path.isfile(src_path):
            print(f"源文件不存在: {src_path}")
            continue

        # 判断是“现”还是“古”
        if "古" in src:
            base_name = name + "古"
            for suf in suffixes:
                new_name = base_name + suf + ".png"
                dest_path = os.path.join(target_folder, new_name)
                shutil.copyfile(src_path, dest_path)
                print(f"复制: {src} → {new_name}")
        elif "现" in src:
            base_name = name
            for suf in suffixes:
                new_name = base_name + suf + ".png"
                dest_path = os.path.join(target_folder, new_name)
                shutil.copyfile(src_path, dest_path)
                print(f"复制: {src} → {new_name}")
