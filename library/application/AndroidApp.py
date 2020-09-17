from adbutils import adb
from airtest.core.api import device
from airtest.utils.retry import retries
from poco.drivers.android.uiautomation import AndroidUiautomationPoco

from library.application.App import App, retry_connect, check_poco_service
from library.application.VersionManager import VersionManger
from library.utils.thread_utils import StopStatusThread


class AndroidApp(App):
    """
    AndroidApp
    """
    def __init__(self, app_name=None, version_name=None, version_code=None, app_url=None):
        super().__init__("Android", app_name, version_name, version_code, app_url)
        self.check_poco_service = None

    @retries(5)
    def connect(self, driver_ip, driver_port, device_id):

        if driver_ip and driver_port:
            print(adb.connect("{0}:{1}".format(driver_ip, driver_port)))
            if not device_id:
                device_id = "{0}:{1}".format(driver_ip, driver_port)

        if device_id:
            self.device = retry_connect("android:///{0}".format(device_id))
            # self.device = retry_connect("android:///{0}?cap_method=javacap&ori_method=adbori".format(device_id))

        driver = AndroidUiautomationPoco(self.device, poll_interval=1)
        self.device = device()
        # 关闭截图
        driver.screenshot_each_action = True

        return driver

    def check_version(self, version_name, version_code, app_url, is_cover_install=True):
        if not version_name or not version_code:
            return
        version_manger = VersionManger(self.platform, app_url, self.app_name, version_name, version_code)
        version_manger.check_version(self.device.uuid, is_cover_install)

    def connected(self):
        self.check_poco_service = StopStatusThread(check_poco_service)
        self.check_poco_service.client_thread = self.client_thread
        self.check_poco_service.start()

    def finished(self):
        super().finished()
        if self.check_poco_service is not None:
            self.check_poco_service.stop()