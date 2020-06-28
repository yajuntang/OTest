import importlib
import sys

import inspect
import os
import shutil
import threading
import time
import traceback
from typing import List

from adbutils import adb
from airtest.core.api import connect_device, auto_setup, device, set_current, start_app, stop_app, snapshot
from airtest.core.cv import try_log_screen
from airtest.core.helper import using, logwrap, G
from airtest.report.report import LogToHtml, HTML_TPL, LOGFILE
from airtest.utils.compat import script_dir_name
from airtest.utils.retry import retries
from poco import Poco
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from poco.drivers.ios import iosPoco
from tenacity import Retrying, wait_fixed, stop_after_attempt
from wda import WDAError
# pip3 install -U flask_cors  -i https://mirrors.aliyun.com/pypi/simple/

from library.application.Task import PageData
from library.application.VersionManager import VersionManger
from library.base.utils.thread_utils import StopStatusThread, TaskThread


class App:
    platform = None
    driver = None
    device = None
    app_name = None

    def __init__(self, platform, app_name, version_name=None, version_code=None, app_url=None, is_cover_install=False):
        self.platform = platform
        self.app_name = app_name
        self.client_thread = None
        self.version_name = version_name
        self.version_code = version_code
        self.app_url = app_url
        self.is_cover_install = is_cover_install
        self.log_path = None
        self.client = None
        self.task = None
        self.test_result_status = True

    def set_client_task(self, client, task):
        self.client = client
        self.task = task
        return self.log_path

    def start_test(self, pages, ip=None, port=None, device_id=None):

        self.log_path = setup_log_path(create_report_dir(self.platform))
        auto_setup(__file__, logdir=self.log_path)

        if pages is None or len(pages) == 0:
            self.log("没有设置测试页面")
            raise ValueError("没有设置测试页面")
            
        pages = [page for page in map(lambda item: item if isinstance(item,PageData) else PageData(item), pages)]

        if ip:
            url = "{0}:{1}".format(ip, port)
        else:
            url = "{0}".format(device_id)

        self.log_step("应用信息", 'AppId:{0}'.format(self.app_name))
        self.log("应用信息:AppId:{0}".format(self.app_name))

        self.log("开始连接设备:{0}".format(url))

        try:
            self.driver = self.connect(ip, port, device_id)
        except Exception as e:
            self.test_result_status = False
            log = traceback.print_exc()
            print(log)
            self.log_error("连接设备失败")
            self.log_error(traceback.format_exc())
            self.log_step("连接设备", '连接"{0}"失败:{1}'.format(url, e), False, traceback.format_exc())
            raise e

        self.connected()
        self.check_device()
        self.check_version(self.version_name, self.version_code, self.app_url, self.is_cover_install)
        self.log("设备连接成功开始,开始测试.....")
        self.log_step("连接设备", '连接"{0}"成功'.format(url))

        self.do_test(pages)
        name = report(self.task, self.log_path)
        self.upload_report(self.log_path, name)
        self.finished()

        if self.task is not None:
            self.log("{0}已执行完毕，报告已生成".format(self.task.name))
            self.log_step("生成报告", "")

    def do_test(self, pages: List[PageData]):
        for page_info in pages:

            name = page_info.get_log_name()
            log_page_name(name)

            self.log("开始测试页面:{0}【{1}】".format(name, page_info.get_class_name()))

            page = page_info.get_instance()

            if len(page_info.get_page_data()) > 0:
                self.log("参数:{0}".format(page_info.get_page_format_data()))

            self.log_step(name, "参数:{0}".format(page_info.get_page_format_data()), attach=page_info.key)

            self.inject_pages_info(page)
            using(os.path.abspath(os.path.dirname(inspect.getfile(page_info.classes))))

            def log_method_failed(method_name, error, args=()):
                self.log_error("执行{0}::{1}失败".format(name, method_name))
                self.log_error("'{0}'".format(error))
                self.log_step(method_name, '参数:{0}'.format(args), False, error,
                              page_info.get_method_key_by_name(method_name))

            try:
                page.setUpClass()
            except Exception as e:
                self.check_system_exit(e)
                self.test_result_status = False
                print(e)
                traceback.print_exc()
                log_method_failed("setUpClass", traceback.format_exc())

            for m in page_info.get_test_methods():

                try:
                    self.do_test_method(page_info, name, page, m, log_method_failed)
                except BaseException as e:
                    self.check_system_exit(e)
                    print(e)
                    traceback.print_exc()
            try:
                page.tearDownClass()
            except Exception as e:
                if isinstance(e, SystemExit):
                    raise e
                self.check_system_exit(e)
                self.test_result_status = False
                print(e)
                traceback.print_exc()
                log_method_failed("tearDownClass", traceback.format_exc())

    @retries(max_tries=10, exceptions=ZeroDivisionError)
    def do_test_method(self, page_info, name, page, m, log_method_failed):

        try:
            method_args = page_info.get_method_data(m)
            method_args_log = PageData.format_method_log("({0})".format(method_args))
            self.log("执行{0}::{1}".format(name, m.__name__) + method_args_log)
            page.setUp()
        except Exception as e:
            if isinstance(e, ZeroDivisionError):
                raise e
            self.check_system_exit(e)
            self.snapshot()
            self.test_result_status = False
            print(e)
            traceback.print_exc()
            log_method_failed(m.__name__, traceback.format_exc())

            return  # 如果是setUp出现异常 那么就执行下一个用例 后面没必要跑了
        try:
            m(**method_args)
        except Exception as e:
            if isinstance(e, ZeroDivisionError):
                raise e
            self.check_system_exit(e)
            self.snapshot()
            self.test_result_status = False
            print(e)
            traceback.print_exc()
            log_method_failed(m.__name__, traceback.format_exc(), method_args)

        try:
            page.tearDown()
        except Exception as e:
            if isinstance(e, ZeroDivisionError):
                raise e
            self.check_system_exit(e)
            self.snapshot()
            self.test_result_status = False
            print(e)
            traceback.print_exc()
            log_method_failed(m.__name__, traceback.format_exc())

        self.log_step(m.__name__, '参数:{0}'.format(method_args_log))

    def check_device(self):
        if device().uuid != self.device.uuid:
            set_current(self.device.uuid)

    def start_app(self, activity=None):
        self.check_device()
        start_app(self.app_name, activity)

    def snapshot(self, filename=None, msg=''):
        try:
            snapshot(filename=filename, msg=msg)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def stop_app(self):
        self.check_device()
        stop_app(self.app_name)

    def inject_pages_info(self, page):
        page.platform = self.platform
        page.app = self
        page._driver = self.driver
        page.app_name = self.app_name

    def connect(self, driver_ip, driver_port, device_id) -> Poco:
        pass

    def connected(self):
        pass

    def check_version(self, version_name, version_code, app_url, is_cover_install=True):
        pass

    def log(self, log):
        if self.client is None:
            return
        self.client.log(self.task, log)

    def log_step(self, title, sub_title, successful=True, message=None, attach=None):
        if self.client is None:
            return
        self.client.log_step(self.task, title, sub_title, message, attach, successful)

    def log_error(self, log):
        if self.client is None:
            return
        self.client.log_error(self.task, log)

    def upload_report(self, path, name):
        if self.client is None:
            return
        self.client.upload_report(self.task, os.path.join(path, name))

    def finished(self):
        if self.client is None:
            return
        self.client.finished_task(self.task, self.test_result_status)

    def check_system_exit(self, e):
        if isinstance(e,(SystemExit,SystemError)):
            raise e


class AndroidApp(App):

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


def check_poco_service(stopped,client_thread):
    while not stopped:
        if client_thread is not None and client_thread.stopped:
            return
        time.sleep(150)
        start_app('com.netease.open.pocoservice', 'TestActivity')


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
        super().start_test(pages,ip,port,device_id)


def retry_connect(uri=None, whether_retry=False, sleeps=5, max_attempts=3):
    if not whether_retry:
        max_attempts = 1

    r = Retrying(wait=wait_fixed(sleeps), stop=stop_after_attempt(max_attempts), reraise=True)
    try:
        return r(connect_device, uri)
    except Exception as e:
        if isinstance(e, (WDAError,)):
            raise e


def report(task, log_path):
    path, name = script_dir_name(__file__)
    try:
        m = importlib.import_module('config')
        m.__title__ = task.name
        path, name = script_dir_name(m.__file__)
    except:
        try:
            m = importlib.import_module('library.author')
            m.__title__ = task.name
            path, name = script_dir_name(m.__file__)
        except:
            if task is not None:
                path, name = script_dir_name(sys.argv[0])

    static_root = {}
    if task is not None:
        static_root['static_root'] = 'http://localhost:9000/static'

    rpt = LogToHtml(script_root=path, script_name=name, export_dir=log_path, **static_root, log_root=log_path,
                    logfile=LOGFILE, lang="zh",
                    plugins=["poco.utils.airtest.report"])
    rpt.report(HTML_TPL)
    return name.replace('.py', '') + '.log'


def setup_log_path(log_path):
    if os.path.exists(log_path):
        shutil.rmtree(log_path)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    return log_path


def log_page_name(name):
    def log_page_name_func():
        pass

    log_page_name_func.__name__ = name
    logwrap(log_page_name_func)()


def create_report_dir(platform) -> str:
    log_dir = "log/{0}/{1}".format(platform.lower(), (int(time.time())))
    path, name = script_dir_name(__file__)
    log_path = os.path.join(os.path.dirname(os.path.dirname(path)), log_dir)
    return log_path
