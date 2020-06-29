import importlib
import json
import os
import threading
import time
import traceback
from typing import List

from library.application.IOSApp import IOSApp
from library.application.AndroidApp import AndroidApp
from library.client.Task import PageData, Task
from library.utils.thread_utils import stop_thread, TaskThread

__author__ = 'Cheryl'


class Client:

    @staticmethod
    def run(ip, port):
        t = threading.Thread(target=Client.new_client, args=(ip, port), daemon=True)
        t.start()

    @staticmethod
    def new_client(ip, port):
        return Client(ip, port)

    def __init__(self, ip, port):
        self.http = Http(ip, port)
        self.runningThreads: List[TaskThread] = []
        self.runningTask = []
        self.pendingRunTasks = []
        while True:
            try:
                self.check_thread()
                self.get_waited_task_list()
                self.get_pending_stop_list()
            except Exception as e:
                print(e)
                traceback.print_exc()
            time.sleep(2)

    def get_waited_task_list(self):
        waited_tasks = self.http.get_waited_task_list()
        for item in waited_tasks:
            if self.task_is_running(item):
                return
            for pending_run_task in self.pendingRunTasks:
                if pending_run_task.task_id == item.task_id:
                    return
            self.pendingRunTasks.append(item)
            self.start_test_for_task(item)
            self.pendingRunTasks.remove(item)

    def get_pending_stop_list(self):
        tasks = self.http.get_pending_stop_list()
        for item in tasks:
            self.stop_test_for_task(item)

    def stop_test_for_task(self, task: Task):
        self.remove_thread(task)
        try:
            self.runningTask = [item for item in self.runningTask if item.task_id != task.task_id]
            self.http.report_stop(task)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def remove_thread(self, task: Task, need_stop=True):
        try:
            for item in self.runningThreads:
                if item.name == task.device.platform + "/" + task.name + "/" + task.task_id:
                    self.runningThreads.remove(item)
                    if need_stop:
                        stop_thread(item)
                    break
        except Exception as e:
            print(e)
            traceback.print_exc()

    def finished_task(self, task: Task, successful):
        self.remove_thread(task, False)
        self.runningTask = [item for item in self.runningTask if item.task_id != task.task_id]
        self.http.report_finished(task, successful)

    def log(self, task, log):
        try:
            self.http.log(task, log)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def log_error(self, task, log):
        try:
            self.http.log_error(task, log)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def log_step(self, task, title, sub_title, message, attach, successful):
        try:
            self.http.log_step(task, title, sub_title, message, attach, successful)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def task_is_running(self, task):
        for item in self.runningTask:
            if item.task_id == task.task_id:
                return True
        return False

    def check_thread(self):
        for item in self.runningThreads:
            if item.stopped :
                self.stop_test_for_task(item.task)

    def start_test_for_task(self, task: Task):

        try:
            pages = []
            for page_info in task.page_data:
                pages.append(
                    PageData(import_class(page_info['path'], page_info['name']),page_info['path'], page_info['data'],
                             page_info['method_data']))

            dev = task.device

            if dev.platform == 'Android':
                app = AndroidApp(task.app.app_id, task.app.version_name, task.app.version_code, task.app.app_url)
            else:
                app = IOSApp(task.app.app_id)

            task.report_url = app.set_client_task(self, task)
            t = TaskThread(task, app.start_test, pages, dev.ip, dev.port, dev.device_id)
            t.setName(task.device.platform + "/" + task.name + "/" + task.task_id)
            app.client_thread = t
            self.runningThreads.append(t)
            self.runningTask.append(task)
            self.http.report_run(task)
            t.start()
        except Exception as e:
            print(e)
            traceback.print_exc()
            self.stop_test_for_task(task)

    def upload_report(self, task, report_path):
        def listdir(path, parent_dir, files):
            for file in os.listdir(path):
                if file in ('.DS_Store', "__pycache__"):
                    continue
                file_path = os.path.join(path, file)
                if os.path.isdir(file_path):
                    listdir(file_path, os.path.join(parent_dir, file), files)
                else:
                    files[os.path.join(parent_dir, file)] = open(file_path, 'rb')

        files = {}
        listdir(report_path, "", files)
        if len(files) == 0: return
        self.http.upload_report(task, files)


import requests

timeout = 30


class Http:

    def __init__(self, ip, port):
        self.base_url = 'http://{0}:{1}'.format(ip, port)

    def get_waited_task_list(self):
        response = requests.get(url=self.base_url + '/get_waited_task', timeout=timeout)
        return parse_json_list(response.text, Task)

    def get_pending_stop_list(self):
        response = requests.get(url=self.base_url + '/get_pending_stop_tasks', timeout=timeout)
        return parse_json_list(response.text, Task)

    def report_run(self, task):
        data = {'group_id': task.group_id, 'task_id': task.task_id, 'report_url': task.report_url}
        requests.post(url=self.base_url + "/run_task", json=data, timeout=timeout)

    def report_stop(self, task):
        data = {'group_id': task.group_id, 'task_id': task.task_id}
        requests.post(url=self.base_url + "/stop_task", json=data, timeout=timeout)

    def report_finished(self, task, successful):
        data = {'group_id': task.group_id, 'task_id': task.task_id, 'successful': successful}
        requests.post(url=self.base_url + "/finished_task", json=data, timeout=timeout)

    def log(self, task, log, log_type='info'):
        data = {'group_id': task.group_id, 'task_id': task.task_id, 'log': log, 'log_type': log_type}
        requests.post(url=self.base_url + "/append_task_log", json=data, timeout=timeout)

    def log_error(self, task, log):
        self.log(task, log, 'error')

    def log_step(self, task, title, sub_title, message, attach, successful):
        data = {'group_id': task.group_id, 'task_id': task.task_id, 'title': title, 'sub_title': sub_title,
                "message": message, 'attach': attach, 'successful': successful}
        requests.post(url=self.base_url + "/append_task_step", json=data, timeout=timeout)

    def upload_report(self, task, files):
        headers = {'group_id': task.group_id, 'task_id': task.task_id}
        requests.post(url=self.base_url + "/upload_report", headers=headers, files=files)


def parse_json_list(data, classes):
    data_list = []
    if data is None:
        return data_list
    try:
        if 'data' in data:
            json_data = json.loads(data)
            json_data = json_data['data']
            for item in json_data:
                data_list.append(classes.parse(item))
    except BaseException as e:
        print(e)
        traceback.print_exc()
    return data_list


def import_class(class_path: str, name: str):
    module_path = class_path.replace('.' + name, "")
    module = importlib.import_module(module_path)
    classes = getattr(module, name)
    return classes
