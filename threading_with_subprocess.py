"""
Experiment to show that subprocesses aren't affected by the GIL (of course)
So we can start multiple C++ processes from Python threads, and have them execute in parallel
"""

import subprocess
import time
from threading import Thread


def run_cpp_sleep() -> None:
    subprocess.run('./sleep')


def main() -> None:
    start_time = time.time()
    thread1 = Thread(target=run_cpp_sleep)
    thread2 = Thread(target=run_cpp_sleep)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    print(f"Time taken={time.time() - start_time}")


if __name__ == '__main__':
    main()
