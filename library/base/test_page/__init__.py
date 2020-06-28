from airtest.core.api import shell, snapshot as airtest_snapshot, home, sleep, assert_not_equal, assert_equal
from poco import Poco

from library.base.ui.UI import UI, UI_TIME_OUT


class TestPage:
    platform = "Android"
    app = None
    _driver: Poco = None
    app_name = ""

    def __getattribute__(self, attr):

        _dict = object.__getattribute__(self, '__dict__')

        if attr in _dict:
            ui = _dict[attr]
            if isinstance(ui, UI):
                self.set_ui(ui)
                return ui
            if isinstance(ui, list):
                for ui_item in ui:
                    if isinstance(ui_item, UI):
                        self.set_ui(ui_item)
                return ui

        return object.__getattribute__(self, attr)

    def set_ui(self, ui) -> UI:
        ui.setUp(self._driver, self.platform == "IOS")
        return ui

    def wait_for_any(self, objects, timeout=UI_TIME_OUT) -> UI:
        return self._driver.wait_for_any(objects, timeout)

    def wait_for_all(self, objects, timeout=UI_TIME_OUT):
        return self._driver.wait_for_all(objects, timeout)

    def assert_for_any(self, objects, msg="", timeout=UI_TIME_OUT):
        ui = self.wait_for_any(objects, timeout)
        ui.assert_exists(msg)
        self.snapshot_catch()

    def freeze(self):
        return self._driver.freeze()

    def wait_stable(self):
        self._driver.wait_stable()

    def scroll(self, direction='vertical', percent=0.6, duration=2.0):
        return self._driver.scroll(direction, percent, duration)

    def pinch(self, direction='in', percent=0.6, duration=2.0, dead_zone=0.1):
        return self._driver.pinch(direction, percent, duration, dead_zone)

    @classmethod
    def snapshot(cls, fileName=None, msg=""):
        airtest_snapshot(fileName, msg)

    @classmethod
    def snapshot_catch(cls, fileName=None, msg=""):
        try:
            airtest_snapshot(fileName, msg)
        except:
            pass

    def sleep(self, secs: float):
        sleep(secs)

    @classmethod
    def command(cls, cmd):
        shell(cmd)

    def home(self):
        home()

    def scroll_down(self):
        self._driver.scroll('vertical', 0.3, 1)

    def assert_equal(self, first, second, msg=""):
        assert_equal(first, second, msg)

    def assert_not_equal(self, first, second, msg=""):
        assert_not_equal(first, second, msg)

    def get_screen_size(self):
        return self._driver.get_screen_size()

    def setUp(self):
        self.app.stop_app()
        self.app.start_app()

    def tearDown(self):
        self.app.stop_app()

    def setUpClass(self):
        pass

    def tearDownClass(self):
        pass

    def is_ios_device(self):
        return self.platform == "IOS"

