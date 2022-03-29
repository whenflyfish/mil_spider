# encoding: UTF-8
import threading
import time

def showfun(n):
    print ("%s start -- %d"%(time.ctime(),n))
    print ("working")
    time.sleep(2)
    print ("%s end -- %d" % (time.ctime(), n))


if __name__ == '__main__':
    print()
