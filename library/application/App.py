import importlib
import sys

import inspect
import os
import shutil
import time
import traceback
from typing import List

from airtest.core.api import connect_device, auto_setup, device, set_current, start_app, stop_app, snapshot
from airtest.core.helper import using, logwrap
from airtest.report.report import LogToHtml, HTML_TPL, LOGFILE
from airtest.utils.compat import script_dir_name
from airtest.utils.retry import retries
from poco import Poco
from tenacity import Retrying, wait_fixed, stop_after_attempt
from wda import WDAError

from library.client.Task import PageData


class App:
    """
    框架主体
    """
    platform = None
    driver = None
    device = None
    app_name = None

    def __init__(self, platform, app_name, version_name=None, version_code=None, app_url=None, is_cover_install=False):
        """
        初始化
        :param platform: 平台 Android IOS
        :param app_name: app的包名
        :param app_url: app的安装路径
        """
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
        self.test_result_status = True #本次测试是否成功，但凡有一个测试用例报错都算失败

    def set_client_task(self, client, task):
        """
        如果有时候前端页面，连接将会保存在client中
        :param client: 客户端
        :param task: 任务
        :return: 日志地址
        """
        self.client = client
        self.task = task
        return self.log_path

    def start_test(self, pages, ip=None, port=None, device_id=None):

        """
        开始测试
        :param pages: 待测试的页面列表
        :param ip: 测试手机的IP地址 option
        :param port: 测试手机的端口号 option
        :param device_id: 测试手机的设备id option
        :return:
        """
        self.log_path = setup_log_path(create_report_dir(self.platform))
        auto_setup(__file__, logdir=self.log_path)

        if pages is None or len(pages) == 0:
            self.log("没有设置测试页面")
            raise ValueError("没有设置测试页面")

        pages = [page for page in map(lambda item: item if isinstance(item, PageData) else PageData(item), pages)]

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
        """
        执行测试
        :param pages: 带数据的Page
        :return:
        """
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
                    self.do_test_method(page_info, page, m, log_method_failed)
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
    def do_test_method(self, page_info, page, m, log_method_failed):
        """
        执行测试方法
        :param page_info: 装载执行测试的页面信息
        :param page: 执行测试的页面
        :param m: 执行测试的方法
        :param log_method_failed: 执行测试方法失败后的回调
        :return:
        """

        try:
            method_args = page_info.get_method_data(m)
            method_args_log = PageData.format_method_log("({0})".format(method_args))
            self.log("执行{0}::{1}".format(page_info.get_log_name(), m.__name__) + method_args_log)
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
        """
        启动app
        :param activity: 启用的页面 only android
        :return:
        """
        self.check_device()
        start_app(self.app_name, activity)

    def snapshot(self, filename=None, msg=''):
        """
        截图
        :param filename: 文件名称，可以为空 默认是使用时间作为文件的名字
        :param msg: 截图注释
        :return:
        """
        try:
            snapshot(filename=filename, msg=msg)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def stop_app(self):
        """
        杀掉app
        :return:
        """
        self.check_device()
        stop_app(self.app_name)

    def inject_pages_info(self, page):
        """
        注入页面driver和平台信息
        """
        page.platform = self.platform
        page.app = self
        page._driver = self.driver
        page.app_name = self.app_name
        page.test_case = None

    def connect(self, driver_ip, driver_port, device_id) -> Poco:
        """
        连接设备
        :param driver_ip: 设备IP
        :param driver_port: 设备端口
        :param device_id: 设备id
        :return:
        """
        pass

    def connected(self):
        """
        连接成功的回调
        :return:
        """
        pass

    def check_version(self, version_name, version_code, app_url, is_cover_install=True):
        """
        检测版本
        :param version_name: 版本名称
        :param version_code: 版本号
        :param app_url: 需要下载目标app的链接
        :param is_cover_install: 是否覆盖安装，默认true
        :return:
        """
        pass

    def log(self, log):
        """
        把日志发送到服务器，并记录起来
        :param log:
        :return:
        """
        if self.client is None:
            return
        self.client.log(self.task, log)

    def log_step(self, title, sub_title, successful=True, message=None, attach=None):
        """
        把测试步骤发送服务器，并保存
        :param title: 步骤标题
        :param sub_title: 步骤描述
        :param successful: 记录测试的成功还是失败，用于在前端页面进行回测
        :param message: 异常的错误信息或者正常的信息
        :param attach: 记录此次步骤是哪个页面，哪个方法，用于在前端页面进行回测
        :return:
        """
        if self.client is None:
            return
        self.client.log_step(self.task, title, sub_title, message, attach, successful)

    def log_error(self, log):
        """
        记录错误类型的日志
        :param log: message
        :return:
        """
        if self.client is None:
            return
        self.client.log_error(self.task, log)

    def upload_report(self, path, name):
        """
        把本地生成的报告，上传到服务器
        :param path:
        :param name:
        :return:
        """
        if self.client is None:
            return
        self.client.upload_report(self.task, os.path.join(path, name))

    def finished(self):
        """
        测试结束后，告知服务器
        :return:
        """
        if self.client is None:
            return
        self.client.finished_task(self.task, self.test_result_status)

    def check_system_exit(self, e):
        """
        判断检测android pocoservice的线程 是否退出了
        :param e:
        :return:
        """
        if isinstance(e, (SystemExit, SystemError)):
            raise e


def check_poco_service(stopped, client_thread):
    """
    每隔150 启动 poco_service
    :param stopped:
    :param client_thread:
    :return:
    """
    while not stopped:
        if client_thread is not None and client_thread.stopped:
            return
        time.sleep(150)
        start_app('com.netease.open.pocoservice', 'TestActivity')


def retry_connect(uri=None, whether_retry=False, sleeps=5, max_attempts=3):
    """
    尝试重连，默认三次，每次间隔5秒
    :param uri:
    :param whether_retry:
    :param sleeps:
    :param max_attempts:
    :return:
    """
    if not whether_retry:
        max_attempts = 1

    r = Retrying(wait=wait_fixed(sleeps), stop=stop_after_attempt(max_attempts), reraise=True)
    try:
        return r(connect_device, uri)
    except Exception as e:
        if isinstance(e, (WDAError,)):
            raise e


def report(task, log_path):
    """
    生成报告
    :param task: 前端配置的任务
    :param log_path:日志的路径
    :return:
    """
    path, name = script_dir_name(__file__)
    try:
        m = importlib.import_module('config')
        if task is not None:
            m.__author__ = task.name
        path, name = script_dir_name(m.__file__)
    except:
        try:
            m = importlib.import_module('library.author')
            if task is not None:
                m.__author__ = task.name
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
    """
    设置日志的路径
    :param log_path: 日志的路径
    :return:
    """
    if os.path.exists(log_path):
        shutil.rmtree(log_path)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    return log_path


def log_page_name(name):
    """
    记录当前测试页面的名字
    :param name:
    :return:
    """
    def log_page_name_func():
        pass
    log_page_name_func.__name__ = name
    logwrap(log_page_name_func)()


def create_report_dir(platform) -> str:
    """
    创建报告生成的文件夹
    :param platform: 区分不同的平台
    :return:
    """
    log_dir = "log/{0}/{1}".format(platform.lower(), (int(time.time())))
    path, name = script_dir_name(__file__)
    log_path = os.path.join(os.path.dirname(os.path.dirname(path)), log_dir)
    return log_path
