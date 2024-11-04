import threading
import time

def countdown(name, start):
    for i in range(start, 0, -1):
        print(f"{name} : {i}")
        time.sleep(0.2)

thread1 = threading.Thread(target=countdown, args=("thread 1", 5))
thread2 = threading.Thread(target=countdown, args=("thread 2", 3))

thread1.start()
thread2.start()

thread1.join()
thread2.join()
