from airtest.core.api import device
from poco.drivers.ios import iosPoco

from library.application.App import App, retry_connect


class IOSApp(App):

    def __init__(self, app_name=None):
        super().__init__("IOS", app_name, None, None, None)

    def connect(self, driver_ip, driver_port, device_id):

        if driver_ip and driver_port:
            self.device = retry_connect("ios:///http://{0}:{1}".format(driver_ip, driver_port))

        elif device_id:
            self.device = retry_connect("ios:///http://{0}".format(device_id))

        driver = iosPoco(self.driver, poll_interval=1)
        self.device = device()

        # 关闭截图
        driver.screenshot_each_action = True
        return driver

    def start_test(self, pages, ip='127.0.0.1', port=8081, device_id=None):
        super().start_test(pages, ip, port, device_id)