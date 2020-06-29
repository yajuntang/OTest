class Device:
    def __init__(self, platform, ip, port, device_id):
        self.platform = platform
        self.ip = ip
        self.port = port
        self.device_id = device_id

    @classmethod
    def parse(cls, data):
        device = Device(None, None, None, None)
        device.__dict__ = data
        return device


class AppInfo:
    def __init__(self, app_id, version_name=None, version_code=None, app_url=None):
        self.app_id = app_id
        self.version_name = version_name
        self.version_code = version_code
        self.app_url = app_url

    @classmethod
    def parse(cls, data):
        app_info = AppInfo(None, None, None, None)
        app_info.__dict__ = data
        return app_info


class Task:

    def __init__(self, session_id, group_id, task_id, plan_id, name, device, app_info, time, page_data,
                 report_url=None):
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
        return self.task_id + ".log"

    def get_step_table_name(self):
        return self.task_id + ".step"

    def get_report_db_name(self):
        return self.task_id + "-report"

    def wait(self):
        self.status = "waited"
        return self

    def run(self):
        self.status = "running"
        return self

    def abort(self):
        self.status = 'aborted'
        return self

    def user_stopped(self):
        self.status = 'user_stopped'

    def pending_stop(self):
        self.status = 'pending_stop'

    def successful(self):
        self.status = 'successful'
        return self

    def is_waited(self):
        return self.status == 'waited'

    def is_running(self):
        return self.status == 'running'

    def is_abort(self):
        return self.status == 'aborted'

    def is_pending_stop(self):
        return self.status == 'pending_stop'

    def is_user_stopped(self):
        return self.status == 'user_stopped'

    def is_successful(self):
        return self.status == 'successful'

    @classmethod
    def parse(cls, data):
        task = Task(None, None, None, None, None, None, None, None, None)
        task.__dict__ = data
        device = Device.parse(task.device)
        app_info = AppInfo.parse(task.app)
        task.device = device
        task.app = app_info
        return task


class PageData:

    def __init__(self, classes, key=None, class_data: list = None, method_data=None):
        if method_data is None:
            method_data = []
        self.classes = classes
        self.key = key
        self.class_data = class_data
        self.method_data = method_data
        self.method_node = {}
        self.obj = None

    def get_page_data(self):
        if self.class_data is None:
            return []
        return self.class_data

    def get_page_format_data(self):
        if self.class_data is None:
            return []
        return [data for data in map(lambda x: {x['name']: x['value']}, self.class_data)]

    def get_instance(self):
        obj = self.classes()
        if self.class_data is not None:
            for item in self.class_data:
                if isinstance(item, dict):
                    setattr(obj, item['name'], item['value'])
                else:
                    setattr(obj, item.name, item.value)

        self.obj = obj
        return obj

    def get_test_methods(self):
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
        name = method.__name__
        data = []
        for item in self.method_data:
            if item['name'] == name:
                data = item['data']
                self.method_node[name] = item['path']
        args = self.data_to_dict(data)
        return args

    def get_method_key_by_name(self, name):
        if name in self.method_node:
            return self.method_node[name]

    @staticmethod
    def format_method_log(log):
        return log.replace(":", "=").replace('{', "").replace("}", "")

    @staticmethod
    def data_to_dict(data) -> dict:
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
        doc = self.classes.__doc__
        if doc is None:
            doc = self.classes.__name__
        return doc

    def get_class_name(self):
        return self.classes.__name__
