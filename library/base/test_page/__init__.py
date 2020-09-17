from airtest.core.api import snapshot as airtest_snapshot, home, sleep, assert_not_equal, assert_equal, keyevent
from poco import Poco

from library.base.ui.UI import UI, UI_TIME_OUT


class TestPage:
    """
    测试基页
    """
    platform = "Android"
    app = None
    _driver: Poco = None

    def __getattribute__(self, attr):
        """
        当页面中获取UI的成员变量时，调用UI.setUp注入poco_driver & platform
        :param attr:
        :return:
        """

        _dict = object.__getattribute__(self, '__dict__')

        if attr in _dict:
            ui = _dict[attr]
            if isinstance(ui, UI):
                self.set_ui(ui)
                return ui
            if isinstance(ui, list):
                #  数组的情况
                for ui_item in ui:
                    if isinstance(ui_item, UI):
                        self.set_ui(ui_item)
                return ui

        return object.__getattribute__(self, attr)

    def set_ui(self, ui) -> UI:
        """
        给UI设置driver & platform
        :param ui:
        :return:
        """
        ui.setUp(self._driver, self.platform == "IOS")  # "Android" == "IOS"
        return ui

    def wait_for_any(self, objects, timeout=UI_TIME_OUT) -> UI:
        """
        等待任何一个元素出现，超时则抛出异常
        :param objects: 需要等待出现的元素列表
        :param timeout: 超时时间
        :return:
        """
        return self._driver.wait_for_any(objects, timeout)

    def wait_for_all(self, objects, timeout=UI_TIME_OUT):
        """
        等待所有元素出现，超时则抛出异常
        :param objects: 需要等待出现的元素列表
        :param timeout: 超时时间
        :return:
        """
        return self._driver.wait_for_all(objects, timeout)

    def assert_for_any(self, objects, msg="", timeout=UI_TIME_OUT):
        """
        断言，页面中 存在任意一个元素，超时则抛出异常
        :param objects: 需要断言的元素列表
        :param msg: 断言描述
        :param timeout: 超时时间
        :return:
        """
        ui = self.wait_for_any(objects, timeout)
        ui.assert_exists(msg)
        self.snapshot_catch()

    @classmethod
    def snapshot_catch(cls, fileName=None, msg=""):
        """
        如果截图报错了，就跳过，不会终止
        :param fileName: 文件名称，可以为空，默认按时间作为名称
        :param msg: 消息
        :return:
        """
        try:
            airtest_snapshot(fileName, msg)
        except:
            pass

    def sleep(self, secs: float):
        """
        线程休眠
        :param secs: 休眠时间，单位秒
        :return:
        """
        sleep(secs)

    def home(self):
        """
        回到桌面
        :return:
        """
        home()

    def back(self):
        """
        后退。only android
        :return:
        """
        keyevent("BACK")

    def scroll_down(self, distance=0.3, duration=1):
        """
        向下滚动3分之一的页面距离，时长1秒
        :param distance: 滚动的距离
        :param duration: 时长1秒
        :return:
        """
        self._driver.scroll('vertical', distance, duration)

    def assert_equal(self, first, second, msg=""):
        """
        断言相等
        :param first: anything
        :param second: anything
        :param msg:断言的描述
        :return:
        """
        assert_equal(first, second, msg)

    def assert_not_equal(self, first, second, msg=""):
        """
        断言不相等
        :param first: anything
        :param second: anything
        :param msg:断言的描述
        :return:
        """
        assert_not_equal(first, second, msg)

    def setUp(self):
        """
        数据准备，方法级别
        :return:
        """
        self.app.stop_app()
        self.app.start_app()

    def tearDown(self):
        """
        数据清理，方法级别
        :return:
        """
        self.app.stop_app()

    def setUpClass(self):
        """
        数据准备，class级别
        :return:
        """
        pass

    def tearDownClass(self):
        """
        数据清理，class级别
        :return:
        """
        pass

    def is_ios_device(self):
        """
        当前运行的是否是ios
        :return:
        """
        return self.platform == "IOS"
