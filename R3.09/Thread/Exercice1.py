import threading
import time

def message_thread1():
    for _ in range(5):
        print("Je suis la thread 1")
        time.sleep(0.1)

def message_thread2():
    for _ in range(5):
        print("Je suis la thread 2")
        time.sleep(0.1)

thread1 = threading.Thread(target=message_thread1)
thread2 = threading.Thread(target=message_thread2)

thread1.start()
thread2.start()

thread1.join()
thread2.join()
