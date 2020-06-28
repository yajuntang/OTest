import inspect
import ctypes


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


import threading, traceback, sys


class TaskThread(threading.Thread):  # The timer class is derived from the class threading.Thread
    def __init__(self, task, func, *args):
        threading.Thread.__init__(self)
        self.args = args
        self.func = func
        self.task = task
        self.exitcode = 0
        self.exception = None
        self.exc_traceback = ''
        self.setDaemon(True)
        self.stopped = False

    def run(self):  # Overwrite run() method, put what you want the thread do here
        try:
            self._run()
        except Exception as e:
            self.exitcode = 1  # 如果线程异常退出，将该标志位设置为1，正常退出为0
            self.exception = e
            self.exc_traceback = ''.join(traceback.format_exception(*sys.exc_info()))  # 在改成员变量中记录异常信息

    def _run(self):
        try:
            self.func(*self.args)
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            self.stopped = True


class StopStatusThread(threading.Thread):  # The timer class is derived from the class threading.Thread
    def __init__(self, func, *args):
        threading.Thread.__init__(self)
        self.args = args
        self.func = func
        self.client_thread= None
        self.setDaemon(True)
        self.stopped = False

    def run(self):  # Overwrite run() method, put what you want the thread do here
        self.func(self.stopped,self.client_thread, *self.args)

    def stop(self):
        self.stopped = True
