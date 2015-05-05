from multiprocessing import Process, current_process
import daemon
import time
import celery
from app import tasks


def daemon():
    p = current_process()
    print 'Starting:', p.name, p.pid
    time.sleep(2)
    print 'Exiting :', p.name, p.pid

if __name__ == '__main__':

    d = Process(name='daemon', target=daemon)
    d.daemon = True

    d.start()
    time.sleep(1)