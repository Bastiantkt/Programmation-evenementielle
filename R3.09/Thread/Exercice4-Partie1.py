from multiprocessing import Process
import time

def message_process1():
    for _ in range(5):
        print("Je suis le processus 1")
        time.sleep(0.1)

def message_process2():
    for _ in range(5):
        print("Je suis le processus 2")
        time.sleep(0.1)

if __name__ == '__main__':
    process1 = Process(target=message_process1)
    process2 = Process(target=message_process2)

    process1.start()
    process2.start()

    process1.join()
    process2.join()
