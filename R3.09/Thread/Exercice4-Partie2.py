from multiprocessing import Process
import time

def countdown_process(name, start):
    for i in range(start, 0, -1):
        print(f"{name} : {i}")
        time.sleep(0.2)

if __name__ == '__main__':
    process1 = Process(target=countdown_process, args=("processus 1", 5))
    process2 = Process(target=countdown_process, args=("processus 2", 3))

    process1.start()
    process2.start()

    process1.join()
    process2.join()
