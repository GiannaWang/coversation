import re
##仙界
def process(input_text):
    output = []
    lines = input_text.splitlines()
    for line in lines:
        line = line.strip()

        if line.startswith("【"):
            match = re.match(r'【(.*?)】(.*)', line)
            if match:
                role_name, content = match.groups()
                if "你" in role_name:
                    output.append(f"await ac.sysDialogOn({{roleName: `{role_name}`,content: `{content}`,id: 3260426,hasRoleName: true,hasBg: true,hasRoleAvatar: true,roleAvatarResId: p0,}});")
                else:
                    output.append(f"await ac.sysDialogOn({{roleName: `{role_name}`,content: `{content}`,id: 2411524,hasRoleName: true,hasBg: true,hasRoleAvatar: false,}});")
        else:
            output.append(f"await ac.sysDialogOn({{roleName: `旁白`,content: `{line}`,id: 2411532,hasRoleName: false,hasBg: true,hasRoleAvatar: false,}});")

    return "\n".join(output)
