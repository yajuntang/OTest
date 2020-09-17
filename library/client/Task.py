class Device:
    """
    用于保存前端页面配置的设备连接信息
    """

    def __init__(self, platform, ip, port, device_id):
        self.platform = platform
        self.ip = ip
        self.port = port
        self.device_id = device_id

    @classmethod
    def parse(cls, data):
        """
        dict to class
        :param data: dict
        :return:
        """
        device = Device(None, None, None, None)
        device.__dict__ = data
        return device


class AppInfo:
    """
    保存前端页面配置的需要测试的app的信息
    """

    def __init__(self, app_id, version_name=None, version_code=None, app_url=None):
        self.app_id = app_id
        self.version_name = version_name
        self.version_code = version_code
        self.app_url = app_url

    @classmethod
    def parse(cls, data):
        """
        dict to class
        :param data: dict
        :return:
        """
        app_info = AppInfo(None, None, None, None)
        app_info.__dict__ = data
        return app_info


class Task:
    """
    一个Task代表这一个测试任务
    """

    def __init__(self, session_id, group_id, task_id, plan_id, name, device, app_info, time, page_data,
                 report_url=None):
        """
        初始化
        :param session_id: 此次连接的id
        :param group_id: 测试任务的分组id
        :param task_id: 测试任务的id
        :param plan_id:  测试计划的id
        :param name:   测试任务的名称
        :param device:  需要连接的设备的信息
        :param app_info: 需要测试的app的信息
        :param time:     测试的开始时间
        :param page_data: 需要测试的页面数据列表
        :param report_url: 报告的地址
        """
        self.session_id = session_id
        self.group_id = group_id
        self.task_id = task_id
        self.plan_id = plan_id
        self.name = name
        self.device: Device = device
        self.app: AppInfo = app_info
        self.time = time
        self.report_url = report_url
        self.page_data = page_data
        self.status = None

    def get_log_table_name(self):
        """
        此次任务日志的文件名称
        :return:
        """
        return self.task_id + ".log"

    def get_step_table_name(self):
        """
        此次任务的步骤文件的名称
        :return:
        """
        return self.task_id + ".step"

    def get_report_db_name(self):
        """
        此次任务的报告的文件名称
        :return:
        """
        return self.task_id + "-report"

    def wait(self):
        """
        设置状态:等待
        :return:
        """
        self.status = "waited"
        return self

    def run(self):
        """
        设置状态:运行中
        :return:
        """
        self.status = "running"
        return self

    def abort(self):
        """
        设置状态:异常中断
        :return:
        """
        self.status = 'aborted'
        return self

    def user_stopped(self):
        """
        设置状态:用户停止
        :return:
        """
        self.status = 'user_stopped'

    def pending_stop(self):
        """
        设置状态:预备停止
        :return:
        """
        self.status = 'pending_stop'

    def successful(self):
        """
        设置状态:执行成功
        :return:
        """
        self.status = 'successful'
        return self

    def is_waited(self):
        """
        状态判断:是否等待
        :return:
        """
        return self.status == 'waited'

    def is_running(self):
        """
        状态判断:是否运行中
        :return:
        """
        return self.status == 'running'

    def is_abort(self):
        """
        状态判断:是否中断
        :return:
        """
        return self.status == 'aborted'

    def is_pending_stop(self):
        """
        状态判断:是否预备停止
        :return:
        """
        return self.status == 'pending_stop'

    def is_user_stopped(self):
        """
        状态判断:是否用户停止
        :return:
        """
        return self.status == 'user_stopped'

    def is_successful(self):
        """
        状态判断:是否成功
        :return:
        """
        return self.status == 'successful'

    @classmethod
    def parse(cls, data):
        """
        dict to class
        :param data: dict
        :return:
        """
        task = Task(None, None, None, None, None, None, None, None, None)
        task.__dict__ = data
        device = Device.parse(task.device)
        app_info = AppInfo.parse(task.app)
        task.device = device
        task.app = app_info
        return task


class PageData:
    """
    用于保存待测试页面的页面数据或者方法参数
    """

    def __init__(self, classes, key=None, class_data: list = None, method_data=None):
        """
        初始化，
        :param classes: 待测试页面class
        :param key: 以页面路径+页面class名称作为key
        :param class_data: 页面数据 [{name:name,value:value}]
        :param method_data: 方法数据[{name:test_method_name,data:{name:name,value:value},path:xx.page.method}]
        """
        if method_data is None:
            method_data = []
        self.classes = classes
        self.key = key
        self.class_data = class_data
        self.method_data = method_data
        self.method_node = {}
        self.obj = None

    def get_page_data(self):
        """
        获取页面数据
        :return:
        """
        if self.class_data is None:
            return []
        return self.class_data

    def get_page_format_data(self):
        """
        返回格式化页面数据，目前用于日志的记录
        :return:
        """
        if self.class_data is None:
            return []
        return [data for data in map(lambda x: {x['name']: x['value']}, self.class_data)]

    def get_instance(self):
        """
        返回待测试页面的实例
        :return:
        """
        if self.obj is None:
            self.obj = self.classes()
        if self.class_data is not None:
            for item in self.class_data:
                if isinstance(item, dict):
                    setattr(self.obj, item['name'], item['value'])
                else:
                    setattr(self.obj, item.name, item.value)

        self.obj = self.obj
        if not hasattr(self.obj, 'test_case'):
            self.obj.test_case = None
        return self.obj

    def get_test_methods(self):
        """
        获取页面中test开头的测试方法
        :return:
        """
        test_methods_name = [m for m in self.classes.__dict__ if m.startswith("test")]
        if self.method_data is not None and len(self.method_data) > 0:
            new_test_methods_names = [m for m in map(lambda x: x['name'], self.method_data)]
        else:
            new_test_methods_names = test_methods_name

        test_methods = []
        for item in new_test_methods_names:
            test_methods.append(getattr(self.obj, item))

        return test_methods

    def get_method_data(self, method):
        """
        返回前端页面中测试方法的参数
        :param method:
        :return:
        """
        name = method.__name__
        data = []
        for item in self.method_data:
            if item['name'] == name:
                data = item['data']
                self.method_node[name] = item['path']
        args = self.data_to_dict(data)
        return args

    def get_method_key_by_name(self, name):
        """
        返回测试方法的路径+名称，用于记录测试步骤
        :param name:
        :return:
        """
        if name in self.method_node:
            return self.method_node[name]

    @staticmethod
    def format_method_log(log):
        """
        对测试方法的日志格式化
        :param log:
        :return:
        """
        return log.replace(":", "=").replace('{', "").replace("}", "")

    @staticmethod
    def data_to_dict(data) -> dict:
        """
        将{name:name,value:value}转化成{name:value}
        :param data:
        :return:
        """
        data_dict = {}
        for item in data:
            if isinstance(item, dict):
                if item['value'] is not None:
                    data_dict[item['name']] = item['value']
            else:
                if item.value is not None:
                    data_dict[item.name] = item.value
        return data_dict

    def get_log_name(self):
        """
        获取记录在日志和报告里面的页面名称
        :return:
        """
        doc = self.classes.__doc__
        if doc is None:
            doc = self.classes.__name__
        return doc

    def get_class_name(self):
        """
        获取页面的名称
        :return:
        """
        return self.classes.__name__
