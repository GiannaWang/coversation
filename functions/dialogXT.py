import re

def process_file(filename, output_filename):
    output = []
    len = 0
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()

            # 处理以 `/` 开头的选项
            if line.startswith("/"):
                options = line[1:].split()  # 提取选项并按空格分割
                functions = []
                option_group = []

                for i, option in enumerate(options):
                    func_name = f"function{i + 1 + len}"
                    functions.append(f"async function {func_name}() {{\n\n}}")
                    option_group.append(
                        f"{{ textContent: `{option}`, nResId: '$107970803', sResId: '$107970804', x: 640, y: {500 - i * 100}, clickFunc: {func_name}, }}"
                    )

                len = len + i + 1

                # 生成 `async function` 代码
                output.extend(functions)

                # 生成 `await ac.createOptionGroup` 代码
                output.append("await ac.createOptionGroup({")
                output.append("  name: 'textOptionGroup2',")
                output.append("  defaultComposition: false,")
                output.append("  index: 0,")
                output.append("  inlayer: 'window',")
                output.append("  spacing: 60,")
                output.append("  anchor: { x: 50, y: 50 },")
                output.append("  clickAudio: { resId: '$51403', vol: 80 },")
                output.append("  optionGroup: [")
                output.append(",\n".join(option_group))
                output.append("  ],")
                output.append("});")

            # 处理对话（【角色】文本）
            elif line.startswith("【"):
                match = re.match(r'【(.*?)】(.*)', line)
                if match:
                    role_name, content = match.groups()
                    if "你" in role_name:
                        output.append(f"await ac.sysDialogOn({{roleName: `{role_name}`,content: `{content}`,id: 4423935,hasRoleName: true,hasBg: true,hasRoleAvatar: true,roleAvatarResId: ac.var.p0,}});")
                    else:
                        output.append(f"await ac.sysDialogOn({{roleName: `{role_name}`,content: `{content}`,id: 4330204,hasRoleName: true,hasBg: true,hasRoleAvatar: false,}});")

            # 处理普通旁白文本
            else:
                output.append(f"await ac.sysDialogOn({{roleName: `旁白`,content: `{line}`,id: 4330203,hasRoleName: false,hasBg: true,hasRoleAvatar: false,}});")

    # 写入 output.txt
    with open(output_filename, "w", encoding="utf-8") as output_file:
        output_file.write("\n".join(output))
    # 清空输入文件
    with open(filename, "w", encoding="utf-8") as file:
        file.truncate(0)
# 调用示例
process_file("F:\Desktop\input.txt", "F:\Desktop\output.txt")

