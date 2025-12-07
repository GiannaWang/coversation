import os
import re

# 指定目标目录
target_dir = r"G:\作品\许我万分闪耀\场景"
def delhead():
    # 获取目标目录下的所有文件
    for filename in os.listdir(target_dir):
        if filename.startswith("_"):  # 检查文件名是否以 _ 开头
            new_name = filename[1:]  # 去除第一个字符 "_"
            old_path = os.path.join(target_dir, filename)
            new_path = os.path.join(target_dir, new_name)

            os.rename(old_path, new_path)  # 执行重命名
            print(f"重命名: {filename} → {new_name}")

def deltail():
    # 遍历目标目录中的所有文件
    for filename in os.listdir(target_dir):
        new_name = filename.replace("——", "")  # 删除 "——"

        # 如果文件名以 ".jpg.jpg" 结尾，则替换为 ".jpg"
        if new_name.endswith(".jpg.jpg"):
            new_name = new_name[:-4]  # 去掉最后的 ".jpg"

        # 只有当文件名发生变化时才执行重命名
        if new_name != filename:
            old_path = os.path.join(target_dir, filename)
            new_path = os.path.join(target_dir, new_name)
            os.rename(old_path, new_path)
            print(f"重命名: {filename} → {new_name}")



deltail()

def rename():
    # 遍历目标目录中的所有文件
    for filename in os.listdir(target_dir):
        new_name = filename.replace("_0004s_00", "")  # 删除 "——"

        # 如果文件名以 ".jpg.jpg" 结尾，则替换为 ".jpg"
        if new_name.endswith(".jpg.jpg"):
            new_name = new_name[:-4]  # 去掉最后的 ".jpg"

        # 只有当文件名发生变化时才执行重命名
        if new_name != filename:
            old_path = os.path.join(target_dir, filename)
            new_path = os.path.join(target_dir, new_name)
            os.rename(old_path, new_path)
            print(f"重命名: {filename} → {new_name}")
print("所有符合条件的文件已重命名！")