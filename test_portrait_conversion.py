import os
import sys

FUNCTION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "functions")
sys.path.insert(0, FUNCTION_DIR)

import convertChat
import dialogDL_auto


assistant_output = dialogDL_auto.process("【助理】你好")
agent_output = dialogDL_auto.process("【经纪人（生气）】安排好了")
song_output = convertChat.process("【宋祈明】你好")

assert "resId: ac.var.助理立绘" in assistant_output
assert "resId: ac.var.经纪人立绘" in agent_output
assert "未知角色图片" not in assistant_output + agent_output
assert "roleAvatarResId: '$193851785'" in song_output

print("portrait conversion tests passed")
