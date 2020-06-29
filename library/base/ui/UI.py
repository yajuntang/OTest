from library.base.ui.AbstractUI import AbstractUI, UI_TIME_OUT
from library.base.ui.AirTestUI import AirTestUI


# from library.base.ui.AppiumDriver import AppiumDriver
# from library.base.ui.AppiumUI import AppiumUI


class UI(AbstractUI):
    proxy = None

    def setUp(self, driver, is_ios, test_case):

        # if isinstance(driver, AppiumDriver):
        #     self.proxy = AppiumUI(**self.kw)
        # else:
        self.proxy = AirTestUI(**self.kw)
        self.proxy.setUp(driver, is_ios, test_case)
        if is_ios:
            self.proxy.__call__(**self.iosKw)

        pending_nodes = [node for node in self.pending_nodes if node.is_ios_data == is_ios]

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
        self.proxy = None
        self.kw = kw
        self.iosKw = None
        self.is_ios_data = False
        self.pending_nodes = []

    def __call__(self, *args, **kwargs):
        self.iosKw = kwargs
        self.is_ios_data = True
        return self

    def __getitem__(self, item):

        if self.proxy is not None:
            self.proxy.__getitem__(item)
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.getitem, item))
        return self

    def child(self, name=None, **attrs):
        if self.proxy is not None:
            self.proxy = self.proxy.child(name, **attrs)
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.child, name, **attrs))
        return self

    def children(self):
        if self.proxy is not None:
            self.proxy = self.proxy.children()
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.child))
        return self

    def offspring(self, name=None, **attrs):
        if self.proxy is not None:
            self.proxy = self.proxy.offspring(name, **attrs)
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.offspring, name, **attrs))
        return self

    def sibling(self, name=None, **attrs):
        if self.proxy is not None:
            self.proxy = self.proxy.sibling(name, **attrs)
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.sibling, name, **attrs))
        return self

    def parent(self):
        if self.proxy is not None:
            self.proxy = self.proxy.parent()
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.parent))
        return self

    def freeze(self):
        if self.proxy is not None:
            self.proxy = self.proxy.freeze()
        else:
            self.pending_nodes.append(Node(self.is_ios_data, Node.freeze))
        return self

    # ======================UI=========================#

    def click(self, pos=None):
        return self.proxy.click(pos)

    def exists(self, is_retry=True, sleeps=2, max_attempts=2, **kwargs):
        return self.proxy.exists(is_retry, sleeps, max_attempts, **kwargs)

    def swipe(self, direction, focus=None, duration=0.5):
        return self.proxy.swipe(direction, focus, direction)

    def wait(self, timeout=UI_TIME_OUT, interval=0.5, intervalfunc=None):
        return self.proxy.wait(timeout, interval, intervalfunc)

    def wait_for_appearance(self, timeout=UI_TIME_OUT):
        self.proxy.wait_for_appearance(timeout)

    def wait_for_disappearance(self, timeout=UI_TIME_OUT):
        self.proxy.wait_for_disappearance(timeout)

    def wait_click(self, timeout=UI_TIME_OUT):
        self.proxy.wait_click(timeout)

    def wait_exists(self, timeout=UI_TIME_OUT):
        return self.proxy.wait_exists(timeout)

    def send_keys(self, keys, enter=True, **kw):
        return self.proxy.send_keys(keys, enter, **kw)

    def get_text(self):
        return self.proxy.get_text()

    def clear(self):
        self.proxy.clear()

    def find(self, direction='vertical', percent=0.3, duration=1.0, timeout=UI_TIME_OUT):
        self.proxy.find(direction, percent, duration, timeout)

    def assert_not_exists(self, msg=""):
        self.proxy.assert_not_exists(msg)

    def assert_exists(self, msg=""):
        self.proxy.assert_exists(msg)


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
