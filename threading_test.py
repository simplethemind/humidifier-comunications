from threading import Timer
import time

def work(container):
    container[0] = True

a = [False]
t = Timer(2.0, work, args=(a,))
t.start()

while not a[0]:
    print ("Waiting, a[0]={0}...".format(a[0]))
    time.sleep(1)

print ("Done, result: {0}.".format(a[0]))