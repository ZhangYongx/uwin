from threading import Thread
import time


def timer(name, delay, repeat):
	print("Timer: " + name + " Started")
	while repeat> 0:
		time.sleep(delay)