from concurrent.futures import ThreadPoolExecutor
import time

def countdown_task(name, start):
    for i in range(start, 0, -1):
        print(f"{name} : {i}")
        time.sleep(0.2)

with ThreadPoolExecutor(max_workers=2) as executor:
    executor.submit(countdown_task, "thread 1", 5)
    executor.submit(countdown_task, "thread 2", 3)
