from abc import abstractmethod

UI_TIME_OUT = 120


class AbstractUI:

    @abstractmethod
    def setUp(self, driver, is_ios,test_case):
        pass

    @abstractmethod
    def __call__(self, *args, **kwargs):
        return self

    @abstractmethod
    def __getitem__(self, item):
        return self

    @abstractmethod
    def child(self, name=None, **attrs):
        return self

    @abstractmethod
    def children(self):
        return self

    @abstractmethod
    def offspring(self, name=None, **attrs):
        return self

    @abstractmethod
    def sibling(self, name=None, **attrs):
        return self

    @abstractmethod
    def parent(self):
        return self

    @abstractmethod
    def freeze(self):
       return self

    # ======================UI=========================#

    @abstractmethod
    def click(self):
        return

    @abstractmethod
    def exists(self, is_retry=True, sleeps=2, max_attempts=2, **kwargs):
        return

    @abstractmethod
    def swipe(self, direction, focus=None, duration=0.5):
        return

    @abstractmethod
    def wait(self, timeout=UI_TIME_OUT, interval=0.5, intervalfunc=None):
        return

    @abstractmethod
    def wait_for_appearance(self, timeout=UI_TIME_OUT):
       pass

    @abstractmethod
    def wait_for_disappearance(self, timeout=UI_TIME_OUT):
        pass

    @abstractmethod
    def wait_click(self, timeout=UI_TIME_OUT):
        pass

    @abstractmethod
    def wait_exists(self, timeout=UI_TIME_OUT):
        return True

    @abstractmethod
    def send_keys(self, keys, enter=True, **kw):
        return

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def get_text(self):
        pass

    @abstractmethod
    def find(self, direction='vertical', percent=0.3, duration=1.0, timeout=UI_TIME_OUT):
        pass

    @abstractmethod
    def assert_not_exists(self, msg=""):
        pass

    @abstractmethod
    def assert_exists(self, msg=""):
        pass
