import time

from airtest.core.api import touch, wait as airtest_wait, sleep, text, loop_find, swipe as airtest_swipe, \
    snapshot as airtest_snapshot
from airtest.core.error import TargetNotFoundError
from airtest.core.helper import logwrap
from poco import Poco
from poco.exceptions import PocoNoSuchNodeException, PocoTargetRemovedException, PocoTargetTimeout
from poco.proxy import UIObjectProxy
from tenacity import Retrying, retry_if_exception_type, wait_fixed, stop_after_attempt

from library.base.ui.AbstractUI import AbstractUI, UI_TIME_OUT
from library.base.ui.UI import Node



class AirTestUI(AbstractUI):
    poco: Poco = None
    is_airtest = True
    is_ios = False

    def setUp(self, driver, is_ios, test_case):
        self.poco = driver
        self.is_ios = is_ios
        self.poco_ui = None
        self.temp_pending_nodes.clear()
        self.temp_ios_pending_nodes.clear()

    def __init__(self, **kw):
        self.kw = kw
        self.init_pending_nodes = []
        self.init_ios_pending_nodes = []
        self.temp_pending_nodes = []
        self.temp_ios_pending_nodes = []
        self.poco_ui: UIObjectProxy = None
        self.airtest_ui = None
        self.iosKw = None

    def __call__(self, *args, **kwargs):
        self.iosKw = kwargs
        return self

    def get_ui(self):
        if self.poco is None: return
        # if self.poco_ui is not None: return

        kw = self.kw if not self.is_ios else self.iosKw
        if kw is None: kw = self.kw

        self.kw = kw

        self.is_airtest = 'img' in kw

        if self.is_airtest:
            self.airtest_ui = kw['img']
        else:
            self.poco_ui = self.poco(**kw)
            pending_nodes = self.init_pending_nodes if not self.is_ios else self.init_ios_pending_nodes
            if pending_nodes.__len__() > 0:
                for node in pending_nodes:
                    self.do_pending(node)
            pending_nodes = self.temp_pending_nodes if not self.is_ios else self.temp_ios_pending_nodes
            if pending_nodes.__len__() > 0:
                for node in pending_nodes:
                    self.do_pending(node)
        return self

    def __getitem__(self, item):
        self.get_pending_nodes().append(Node(Node.getitem, item))
        return self

    def child(self, name=None, **attrs):
        self.get_pending_nodes().append(Node(Node.child, name, **attrs))
        self.get_ui()
        return self

    def children(self):
        self.get_pending_nodes().append(Node(Node.children))
        self.get_ui()
        return self

    def offspring(self, name=None, **attrs):
        self.get_pending_nodes().append(Node(Node.offspring, name, **attrs))
        self.get_ui()
        return self

    def sibling(self, name=None, **attrs):
        self.get_pending_nodes().append(Node(Node.sibling, name, **attrs))
        self.get_ui()
        return self

    def parent(self):
        self.get_pending_nodes().append(Node(Node.parent))
        self.get_ui()
        return self

    def do_pending(self, node):
        if node.node_type == Node.parent:
            self.poco_ui = self.poco_ui.parent()
        elif node.node_type == Node.getitem:
            @logwrap
            def get_item():
                self.poco_ui = self.poco_ui.__getitem__(node.name)
            get_item()

        elif node.node_type == Node.children:
            self.poco_ui = self.poco_ui.children()
        elif node.node_type == Node.child:
            self.child(node.name, **node.kw)
            self.poco_ui = self.poco_ui.child(node.name, **node.kw)
        elif node.node_type == Node.sibling:
            self.poco_ui = self.poco_ui.sibling(node.name, **node.kw)
        elif node.node_type == Node.offspring:
            self.poco_ui = self.poco_ui.offspring(node.name, **node.kw)

    def get_pending_nodes(self):
        if not self.is_ios:
            return self.temp_pending_nodes
        else:
            return self.temp_ios_pending_nodes

    # ======================UI=========================#

    def click(self,focus=None):
        self.get_ui()
        if self.is_airtest:
            return self._air_touch()
        else:
            @logwrap
            def click():
                return self.poco_ui.click(focus)

            return click()

    def click_without_pic(self):
        self.get_ui()
        if self.is_airtest:
            return self._air_touch()
        else:
            return self.poco_ui.click()

    def exists(self, is_retry=True, sleeps=2, max_attempts=2, **kwargs):
        self.get_ui()
        self._exists(is_retry, sleeps, max_attempts, **kwargs)

    def swipe(self, direction, focus=None):
        self.get_ui()

        def _direction_vector_of(dir_):
            if dir_ == 'up':
                dir_vec = [0, -0.1]
            elif dir_ == 'down':
                dir_vec = [0, 0.1]
            elif dir_ == 'left':
                dir_vec = [-0.1, 0]
            elif dir_ == 'right':
                dir_vec = [0.1, 0]
            elif type(dir_) in (list, tuple):
                dir_vec = dir_
            else:
                raise TypeError('Unsupported direction type {}. '
                                'Only "up/down/left/right" or 2-list/2-tuple available.'.format(type(dir_)))
            return dir_vec

        @logwrap
        def swipe(direction, focus):
            pos = self.poco_ui.get_position(focus)
            vector = _direction_vector_of(direction)
            return airtest_swipe(pos, vector=vector)

        return swipe(direction, focus)

    def wait(self, timeout=UI_TIME_OUT, interval=0.5, intervalfunc=None):
        self.get_ui()
        if self.is_airtest:
            airtest_wait(self.airtest_ui, timeout, interval, intervalfunc)
        else:
            @logwrap
            def wait():
                return self.poco_ui.wait(timeout) is not None

            return wait()

    def wait_for_appearance(self, timeout=UI_TIME_OUT):
        self.get_ui()
        if self.is_airtest:
            airtest_wait(self.airtest_ui, timeout)
        else:
            @logwrap
            def wait_for_appearance(timeout):
                self.poco_ui.wait_for_appearance(timeout)

            wait_for_appearance(timeout)

    def wait_for_disappearance(self, timeout=UI_TIME_OUT):
        @logwrap
        def wait_for_disappearance(timeout):
            start = time.time()
            while self.exists():
                self.poco.sleep_for_polling_interval()
                self.get_ui()
                if time.time() - start > timeout:
                    raise PocoTargetTimeout('disappearance', self)

        self.get_ui()
        wait_for_disappearance(timeout)

    def wait_click(self, timeout=UI_TIME_OUT):
        self.wait_for_appearance(timeout)
        self.click()

    def wait_click_without_pic(self, timeout=UI_TIME_OUT):
        self.wait_for_appearance(timeout)
        self.click_without_pic()

    def wait_exists(self, timeout=UI_TIME_OUT):
        try:
            self.wait_for_appearance(timeout)
            return self.exists()
        except Exception:
            return False

    def send_keys(self, keys, enter=True, **kw):
        self.wait_click()
        sleep(0.5)
        if self.is_ios or self.is_airtest:
            text(keys, enter, **kw)
            sleep(0.5)
        else:
            @logwrap
            def send_keys(keys):
                return self.poco_ui.set_text(keys)

            result = send_keys(keys)
            sleep(0.5)
            return result

    def clear(self):

        @logwrap
        def clear():
            self.wait_click()
            sleep(0.5)
            return self.poco_ui.set_text('')

        if self.is_ios:
            ui = AirTestUI(name='delete')
            ui.setUp(self.poco, self.is_ios, None)
            self.poco_ui.long_click()
            ui.wait_click()
        else:
            clear()

    def get_text(self):
        self.get_ui()
        return self.poco_ui.get_text()

    def get_position(self, focus):
        self.get_ui()
        return self.poco_ui.get_position(focus)

    def get_bounds(self):
        self.get_ui()
        return self.poco_ui.get_bounds()

    def child_count(self):
        self.get_ui()
        return len(self.poco_ui.children())

    def get_name(self):
        self.get_ui()
        return self.poco_ui.get_name()

    def find(self, direction='vertical', percent=0.3, duration=0.1, timeout=UI_TIME_OUT):

        def get_ui_safe():
            try:
                self.get_ui()
            except Exception as e:
                self.poco_ui = None
                print(e)

        @logwrap
        def find():
            start = time.time()
            while not self.exists():
                self.poco.scroll(direction, percent, duration)
                self.poco.sleep_for_polling_interval()
                get_ui_safe()
                if time.time() - start > timeout:
                    return

        get_ui_safe()
        find()

    def assert_not_exists(self, msg=""):
        @logwrap
        def assert_not_exists(msg=""):
            try:
                r = self.exists()
                if r:
                    if self.is_airtest:
                        raise AssertionError(
                            "%s exists unexpectedly at pos: %s, message: %s" % (self.airtest_ui, r, msg))
                    else:
                        pos = self.poco_ui.get_position()
                        v = self.poco_ui.query
                        raise AssertionError("%s exists unexpectedly at pos: %s, message: %s" % (v, pos, msg))
            except TargetNotFoundError:
                pass

        assert_not_exists(msg)
        self.snapshot_catch()

    def assert_exists(self, msg=""):
        @logwrap
        def assert_exists(msg=""):
            try:
                r = self.exists()
                if r is False:
                    raise TargetNotFoundError("找不到对象:{0}".format(self.kw))
            except TargetNotFoundError:
                if self.is_airtest:
                    raise AssertionError("%s does not exist in screen, message: %s" % (self.airtest_ui, msg))
                else:
                    v = self.poco_ui.query
                    raise AssertionError("%s does not exist in screen, message: %s" % (v, msg))

        assert_exists(msg)
        self.snapshot_catch()

    def snapshot_catch(self, fileName=None, msg=""):
        """
        截图，try catch 处理
        :param fileName: 文件名称
        :param msg: 消息
        :return:
        """
        try:
            airtest_snapshot(fileName, msg)
        except:
            pass

    # =======================================================================================#

    def _exists(self, is_retry=True, sleeps=2, max_attempts=2, **kwargs):

        """
        Check whether given target exists on device screen

        判断是否存在，默认重试2次，每次停顿2秒
        :param is_retry: 是否重试
        :param sleeps: 每次停顿时间
        :param max_attempts: 2次
        :return:
        """

        @logwrap
        def exists():
            count = max_attempts
            if not is_retry:
                count = 1

            def air_retry_exists():
                return loop_find(self.airtest_ui, timeout=UI_TIME_OUT, **kwargs)

            def poco_retry_exists():
                if self.poco_ui is None:
                    self.get_ui()
                    return False
                return self.poco_ui.attr('visible')

            r = Retrying(retry=retry_if_exception_type(TargetNotFoundError),
                         wait=wait_fixed(sleeps),
                         stop=stop_after_attempt(count),
                         reraise=True)
            try:
                res = r(r, air_retry_exists if self.is_airtest else poco_retry_exists)
            except (PocoTargetRemovedException, PocoNoSuchNodeException, TargetNotFoundError):
                res = False

            return res

        return exists()

    def _air_touch(self, is_retry=True, sleeps=2, max_attempts=2, **kwargs):
        if not is_retry:
            max_attempts = 1

        r = Retrying(retry=retry_if_exception_type(TargetNotFoundError),
                     wait=wait_fixed(sleeps),
                     stop=stop_after_attempt(max_attempts),
                     reraise=True)
        try:
            r(r, touch, self.airtest_ui, **kwargs)
        except Exception as e:
            raise e
