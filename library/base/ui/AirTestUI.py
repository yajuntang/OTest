import time

from airtest.core.api import touch, wait as airtest_wait, sleep, text,loop_find, swipe as swipe_airtest,snapshot as airtest_snapshot
from airtest.core.error import TargetNotFoundError
from airtest.core.helper import logwrap
from poco import Poco
from poco.exceptions import PocoNoSuchNodeException, PocoTargetRemovedException, PocoTargetTimeout
from poco.proxy import UIObjectProxy
from tenacity import Retrying, retry_if_exception_type, wait_fixed, stop_after_attempt

from library.base.ui.AbstractUI import AbstractUI

UI_TIME_OUT = 120


class AirTestUI(AbstractUI):
    poco: Poco = None
    is_airtest = True

    def setUp(self, driver, is_ios,test_case):
        self.poco = driver
        kw = self.kw if not is_ios else self.iosKw
        if kw is None: kw = self.kw

        self.kw = kw

        pending_nodes = [node for node in self.pending_nodes if node.is_ios_data == is_ios]

        self.is_airtest = 'img' in kw

        if self.is_airtest:
            self.airtest_ui = kw['img']
            self.pending_nodes.clear()
        else:
            self.poco_ui = driver(**kw)
            if pending_nodes.__len__() > 0:
                for node in pending_nodes:
                    if node.node_type == Node.parent:
                        self.parent()
                    elif node.node_type == Node.getitem:
                        self.__getitem__(node.name)
                    elif node.node_type == Node.children:
                        self.children()
                    elif node.node_type == Node.child:
                        self.child(node.name, **node.kw)
                    elif node.node_type == Node.sibling:
                        self.sibling(node.name, **node.kw)
                    elif node.node_type == Node.offspring:
                        self.offspring(node.name, **node.kw)
                    elif node.node_type == Node.freeze:
                        self.freeze()

    def __init__(self, **kw):
        self.kw = kw
        self.pending_nodes = []
        self.poco_ui: UIObjectProxy = None
        self.airtest_ui = None
        self.is_ios_data = False
        self.iosKw = None

    def __call__(self, *args, **kwargs):
        self.iosKw = kwargs
        self.is_ios_data = True
        return self

    def __getitem__(self, item):
        if self.poco_ui is not None:
            try:
                self.wait()
            except Exception:
                pass
            self.poco_ui = self.poco_ui.__getitem__(item)
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.getitem, item))
        return self

    def child(self, name=None, **attrs):
        if self.poco_ui is not None:
            self.poco_ui = self.poco_ui.child(name, **attrs)
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.child, name, **attrs))
        return self

    def children(self):
        if self.poco_ui is not None:
            self.poco_ui = self.poco_ui.children()
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.children))
        return self

    def offspring(self, name=None, **attrs):
        if self.poco_ui is not None:
            self.poco_ui = self.poco_ui.offspring(name, **attrs)
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.offspring, name, **attrs))
        return self

    def sibling(self, name=None, **attrs):
        if self.poco_ui is not None:
            self.poco_ui = self.poco_ui.sibling(name, **attrs)
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.sibling, name, **attrs))
        return self

    def parent(self):
        if self.poco_ui is not None:
            self.poco_ui = self.poco_ui.parent()
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.parent))
        return self

    def freeze(self):
        if self.poco_ui is not None:
            with self.poco.freeze() as freeze:
                self.poco_ui = freeze(**self.kw)
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.freeze))
        return self

    # ======================UI=========================#

    def click(self):
        if self.is_airtest:
            return self._air_touch()
        else:
            @logwrap
            def click():
                return self.poco_ui.click()

            return click()

    def exists(self, is_retry=True, sleeps=2, max_attempts=2, **kwargs):
        if self.is_airtest:
            return self._air_exists(is_retry, sleeps, max_attempts, **kwargs)
        else:
            return self._poco_exists(is_retry, sleeps, max_attempts)

    def swipe(self, direction, focus=None, duration=0.5):
        @logwrap
        def swipe(direction, focus, duration):
            return self.poco_ui.swipe(direction, focus, duration)

        return swipe(direction, focus, duration)

    def airtest_swipe(self, v2=None, vector=None, **kwargs):
        return swipe_airtest(self.airtest_ui, v2, vector, kwargs)

    def wait(self, timeout=UI_TIME_OUT, interval=0.5, intervalfunc=None):
        if self.is_airtest:
            airtest_wait(self.airtest_ui, timeout, interval, intervalfunc)
        else:
            @logwrap
            def wait():
                return self.poco_ui.wait(timeout) is not None

            return wait()

    def wait_for_appearance(self, timeout=UI_TIME_OUT):
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
                if time.time() - start > timeout:
                    raise PocoTargetTimeout('disappearance', self)

        wait_for_disappearance(timeout)

    def wait_click(self, timeout=UI_TIME_OUT):
        self.wait_for_appearance(timeout)
        self.click()

    def wait_exists(self, timeout=UI_TIME_OUT):
        try:
            self.wait_for_appearance(timeout)
            return self.exists()
        except Exception:
            return False

    def send_keys(self, keys, enter=True, **kw):
        self.wait_click()
        sleep(0.5)
        if self.is_ios_data or self.is_airtest:
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
        self.wait_click()
        sleep(0.5)

        @logwrap
        def clear():
            return self.poco_ui.set_text('')
        clear()
        sleep(0.5)

    def get_text(self):
        return self.poco_ui.get_text()

    def find(self, direction='vertical', percent=0.3, duration=1.0, timeout=UI_TIME_OUT):
        @logwrap
        def find():
            start = time.time()
            while not self.exists():
                self.poco.scroll(direction, percent, duration)
                self.poco.sleep_for_polling_interval()
                if time.time() - start > timeout:
                    return

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
        try:
            airtest_snapshot(fileName, msg)
        except:
            pass



    # =======================================================================================#

    def _poco_exists(self, is_retry=True, sleeps=2, max_attempts=2):
        @logwrap
        def exists():
            count = max_attempts
            if not is_retry:
                count = 1

            def retry_exists():
                return self.poco_ui.attr('visible')

            r = Retrying(retry=retry_if_exception_type(TargetNotFoundError),
                         wait=wait_fixed(sleeps),
                         stop=stop_after_attempt(count),
                         reraise=True)
            try:
                res = r(r, retry_exists)
            except (PocoTargetRemovedException, PocoNoSuchNodeException):
                res = False

            return res

        return exists()

    def _air_exists(self, is_retry=True, sleeps=2, max_attempts=2, **kwargs):
        if not is_retry:
            max_attempts = 1

        def retry_exists():
            return loop_find(self.airtest_ui, timeout=UI_TIME_OUT, **kwargs)

        r = Retrying(retry=retry_if_exception_type(TargetNotFoundError),
                     wait=wait_fixed(sleeps),
                     stop=stop_after_attempt(max_attempts),
                     reraise=True)
        try:
            res = r(r, retry_exists)
        except TargetNotFoundError:
            res = False
        return res

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


class Node:
    parent = 0
    sibling = 1
    child = 2
    children = 3
    offspring = 4
    getitem = 5
    freeze = 6

    def __init__(self, is_ios_data, node_type, name=None, **kw):
        self.node_type = node_type
        self.name = name
        self.kw = kw
        self.is_ios_data = is_ios_data
