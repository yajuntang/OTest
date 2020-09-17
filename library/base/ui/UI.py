from library.base.ui.AbstractUI import AbstractUI, UI_TIME_OUT
from library.base.ui.AirTestUI import AirTestUI


class UI(AbstractUI):

    def setUp(self, driver, is_ios, test_case):
        """
          setUp方法 设置driver和 平台
          :param driver: poco driver
          :param is_ios: 平台
          :param test_case: 当前正在测试的页面
          :return:
          """
        self.driver = driver
        self.is_ios = is_ios
        self.proxy = AirTestUI(**self.kw)(**self.iosKw)
        self.proxy.setUp(driver, is_ios, test_case)

        self.proxy.init_pending_nodes = self.pending_nodes
        self.proxy.init_ios_pending_nodes = self.ios_pending_nodes

    def __init__(self, **kw):
        """
        初始化
        :param kw: 保存安卓元素
        """
        self.proxy = None
        self.kw = kw  # 保存Android的元素信息
        self.iosKw = None
        self.pending_nodes = []
        self.ios_pending_nodes = []
        self.proxy: AbstractUI = None
        self.driver = None
        self.test_case = None
        self.is_ios = None

    def __call__(self, *args, **kwargs):
        """
        初始化
        :param args:
        :param kwargs:保存ios元素
        :return: self
        """
        self.iosKw = kwargs  # 保存IOS的元素信息
        return self

    def __getitem__(self, item):
        """
        获取列表
        :param item: 数组下标
        :return:
        """
        self.check_pending(Node(Node.getitem, item))
        return self

    def child(self, name=None, **attrs):
        """
        获取指定定某个孩子
        :param name:
        :param attrs:
        :return:
        """
        self.check_pending(Node(Node.child, name, **attrs))
        return self

    def children(self):
        """
        获取所有孩子，复数，结合列表使用
        :return:
        """
        self.check_pending(Node(Node.children))
        return self

    def offspring(self, name=None, **attrs):
        """
        获取孙子
        :param name:
        :param attrs:
        :return:
        """
        self.check_pending(Node(Node.offspring, name, **attrs))
        return self

    def sibling(self, name=None, **attrs):
        """
        获取兄弟
        :param name:
        :param attrs:
        :return:
        """
        self.check_pending(Node(Node.sibling, name, **attrs))
        return self

    def parent(self):
        """
        获取父节点
        :return:
        """
        self.check_pending(Node(Node.parent))
        return self

    def check_pending(self, node):
        """
        如果已经setup了，说明再使用，直接do_pending就可以了
        :param node:
        :return:
        """
        if self.proxy is None:
            self.get_pending_nodes().append(node)
        else:
            self.do_pending(node)

    def do_pending(self, node):
        """
        根据node执行对应的操作
        :param node:
        :return:
        """
        if node.node_type == Node.parent:
            self.proxy.parent()
        elif node.node_type == Node.getitem:
            self.proxy.__getitem__(node.name)
        elif node.node_type == Node.children:
            self.proxy.children()
        elif node.node_type == Node.child:
            self.child(node.name, **node.kw)
            self.proxy.child(node.name, **node.kw)
        elif node.node_type == Node.sibling:
            self.proxy.sibling(node.name, **node.kw)
        elif node.node_type == Node.offspring:
            self.proxy.offspring(node.name, **node.kw)

    def get_pending_nodes(self):
        """
        根据平台选择pending_nodes,这个是用来记录初始化时的节点关系，
        因为这时候还有driver 无法获取元素，setup之后才去获取
        :return:
        """
        if self.driver is None:
            if self.iosKw is None:
                return self.pending_nodes
            else:
                return self.ios_pending_nodes

    # ======================UI=========================#

    def click(self, focus):
        """
        执行该元素的点击事件
        :param focus:
        :return:
        """
        return self.proxy.click(focus)

    def exists(self, is_retry=True, sleeps=2, max_attempts=2, **kwargs):
        """
        判断是否存在，默认重试2次，每次停顿2秒
        :param is_retry: 是否重试
        :param sleeps: 每次停顿时间
        :param max_attempts: 2次
        :param kwargs:
        :return:
        """
        return self.proxy.exists(is_retry, sleeps, max_attempts, **kwargs)

    def swipe(self, direction, focus=None):
        """
        滑动
        :param direction: 方向
        :param focus: 焦点
        :return:
        """
        return self.proxy.swipe(direction, focus)

    def wait(self, timeout=UI_TIME_OUT, interval=0.5, intervalfunc=None):
        """
        等待
        :param timeout: 超时时间
        :param interval: 轮询间隔
        :param intervalfunc: 每次轮询的回调
        :return:
        """
        return self.proxy.wait(timeout, interval, intervalfunc)

    def wait_for_appearance(self, timeout=UI_TIME_OUT):
        """
        等待出现
        :param timeout: 超时时间
        :return:
        等待元素出现，默认等待超时120秒，Airtest 找不到对象会抛出 TargetNotFoundError，Poco 则是抛出 PocoTargetTimeout
        平台支持:- [x] android- [x] ios
        """
        self.proxy.wait_for_appearance(timeout)

    def wait_for_disappearance(self, timeout=UI_TIME_OUT):
        """
        等待元素消失，默认等待超时120秒,规定时间内 对象仍然存在，则会抛出 PocoTargetTimeout('disappearance', self)
        :param timeout: 超时时间
        :return:
        平台支持:- [x] android- [x] ios
        """
        self.proxy.wait_for_disappearance(timeout)

    def wait_click(self, timeout=UI_TIME_OUT):
        """
        等待点击
        :param timeout: 超时时间
        :return:
        """
        self.proxy.wait_click(timeout)

    def wait_exists(self, timeout=UI_TIME_OUT):
        """
        等待出现后判断存在
        :param timeout: 超时时间
        :return:
        """
        return self.proxy.wait_exists(timeout)

    def send_keys(self, keys, enter=True, **kw):
        """
        发送消息
        :param keys: 内容
        :param enter: 是否回车
        :param kw:
        :return:
        """
        return self.proxy.send_keys(keys, enter, **kw)

    def get_text(self):
        """
        获取元素的text的属性
        :return:
        """
        return self.proxy.get_text()

    def get_ui(self):
        """
        立即调用driver获取元素
        :return:
        """
        return self.proxy.get_ui()

    def get_bounds(self):
        """
        获取元素大小
        :return:
        """
        return self.proxy.get_bounds()

    def get_name(self):
        """
        获取元素的name属性
        :return:
        """
        return self.proxy.get_name()

    def get_position(self, focus):
        """
        获取元素当前的位置坐标
        :return:
        """
        return self.proxy.get_position(focus)

    def child_count(self):
        """
        获取孩子的数量，请确保是最新版的airtest 1.1.4以上
        :return:
        """
        return self.proxy.child_count()

    def clear(self):
        """
        清除输入框的内容，only support Android
        :return:
        """
        self.proxy.clear()

    def find(self, direction='vertical', percent=0.3, duration=0.1, timeout=UI_TIME_OUT):
        """
        当前屏幕查找元素，默认向下滚动
        :param direction: 滑动方向
        :param percent: 滑动的距离
        :param duration: 滑动的时间
        :param timeout: 超时时间
        :return:
        """
        self.proxy.find(direction, percent, duration, timeout)

    def assert_not_exists(self, msg=""):
        """
        断言不存在
        :param msg: 消息
        :return:
        """
        self.proxy.assert_not_exists(msg)

    def assert_exists(self, msg=""):
        """
        断言存在
        :param msg: 消息
        :return:
        """
        self.proxy.assert_exists(msg)


class Node:
    """
    class 保存节点
    """
    parent = 0
    sibling = 1
    child = 2
    children = 3
    offspring = 4
    getitem = 5

    def __init__(self, node_type, name=None, **kw):
        self.node_type = node_type
        self.name = name
        self.kw = kw
