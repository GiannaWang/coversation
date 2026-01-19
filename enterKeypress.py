import time
import datetime
import keyboard

# 设定目标时间（精确到毫秒）
target_time = datetime.datetime.now().replace(
    hour=19, minute=29, second=57, microsecond=740000  # 10:00:00.500
)

# 如果当前时间已经过了今天的目标时间，就等到明天
if datetime.datetime.now() > target_time:
    target_time = target_time + datetime.timedelta(days=1)

print(f"将会在 {target_time.strftime('%H:%M:%S.%f')[:-3]} 按下 Enter")

# 循环等待，直到目标时间
while True:
    now = datetime.datetime.now()
    remaining = (target_time - now).total_seconds()
    if remaining <= 0:
        keyboard.press_and_release('enter')
        print(f"已按下 Enter，时间为 {datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        break
    elif remaining > 1:
        time.sleep(0.5)  # 提前靠近目标时间，降低CPU负担
    else:
        # 最后1秒内，使用更精细的sleep
        time.sleep(0.001)
