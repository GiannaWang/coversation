
rewardtitles = []
rewardconditions = []

with open('rewards.txt', 'r', encoding='utf-8') as file:
    for line in file:
        line = line.strip()
        if '：' in line:  # 确保行中包含冒号
            title, condition = line.split('：', 1)  # 仅分割第一个冒号
            rewardtitles.append(title.strip())
            rewardconditions.append(condition.strip())

print("rewardtitles =", rewardtitles)
print("rewardconditions =", rewardconditions)