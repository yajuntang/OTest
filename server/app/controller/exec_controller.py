import json
import time
from typing import List

from flask import Blueprint, request
from flask_cors import cross_origin

from library.client.Task import Task, Device, AppInfo
from server.app.database.service import service
from server.app.models.models import random_id, PlanModel
from server.app.models.request_models import StartTestRequest, TaskRequest, TaskStepRequest
from server.app.utils import model_request, make_error_response, make_no_data_response, make_response, \
    plan_data_cover_page_data, json_request
from server.server_config import session_id

exec_api = Blueprint("exec_api", __name__)


@exec_api.route("/start_test", methods=['post'])
@model_request(StartTestRequest)
def start_test(data: StartTestRequest):
    """
    开始测试
    :param data:  请求的参数
    :return:
    """
    if data.plan_id is None:
        return make_error_response('请选择计划')

    if data.app_id is None:
        return make_error_response('请选择应用包名')

    plans = service.get_test_plans(data.plan_id)
    if len(plans) == 0:
        return make_error_response('找不到该计划')

    group_id = random_id()  # 随机分配一个group id
    groups: List[Task] = []

    def start_for_task(plan: PlanModel):
        # 从测试计划中获取需要测试的页面
        page_data = service.find_selected_pages_by_plan(plan)
        if len(page_data) == 0:
            return make_error_response('请先在`{0}`中选择要测试的页面'.format(plan.name))

        # 获取页面的数据和测试方法的参数
        for page_data_item in page_data:
            method_data_list = []
            for d in page_data_item['method_data']:
                for method_data in d['data']:
                    method_data_list.append(method_data)
            plan_data_cover_page_data(plan.data, page_data_item['data'], method_data_list)

        # 随机分配一个任务id
        task_id = random_id()
        device = Device(data.platform, data.ip, data.port, data.device_id)
        app_info = AppInfo(data.app_id)
        task = Task(session_id, group_id, task_id, plan.plan_id, plan.name, device, app_info,
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), page_data)
        # 设置为等待测试状态
        task.wait()
        groups.append(task)

    # 一个测试计划里面可能包含多个子测试计划
    for item in plans:
        error_info = start_for_task(item)
        if error_info is not None:
            return error_info

    # 存进数据库中
    service.update_tasks(groups)

    return make_no_data_response()


@exec_api.route("/get_waited_task")
def get_waited_task():
    """
    获取等待测试的列表
    :return:
    """
    # 从数据空获取所有的任务
    groups = service.find_all_group()
    waited_tasks = []
    expire_tasks = []
    for groupId in groups:
        # 获取当前groupId的所有task
        group_tasks = service.find_task_group_by_group_id(groupId)
        # 筛选正在运行的task
        running_task = [t for t in filter(lambda x: x.is_running(), group_tasks)]
        if len(running_task) > 0:
            continue
        waited_task = None
        for task in group_tasks:
            if task.is_waited():
                # 判断是不是此次session的等待，有可能上次还是等待中，但是结束了页面，重新发起新的连接，这时候旧的不要了
                if task.session_id == session_id:
                    if waited_task is None:
                        waited_task = task
                else:
                    task.abort()
                    expire_tasks.append(task)

        if waited_task is not None:
            waited_tasks.append(waited_task)

    if len(expire_tasks) > 0:
        # 过期的任务，更新到数据库中
        service.update_tasks(expire_tasks)
    return make_response(waited_tasks)


@exec_api.route("/start_test_by_task", methods=['post'])
@model_request(TaskRequest)
def start_test_by_task(data: TaskRequest):
    """
    通过一个任务启动测试，一般用于回测
    :param data:
    :return:
    """
    task = service.find_task_by_task_id(data.group_id, data.task_id)
    if task is None:
        return make_error_response('该任务已不存在')
    plan = service.find_plan_by_id(task.plan_id)
    if plan is None:
        return make_error_response('该计划已不存在')

    task.group_id = random_id()
    task.task_id = random_id()
    task.time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    task.session_id = session_id  # 更新为本次的session
    task.wait()
    service.update_task(task)
    return make_no_data_response()


@exec_api.route("/start_error_test_by_task", methods=['post'])
@model_request(TaskRequest)
def start_error_test_by_task(data: TaskRequest):
    """
    运行本次任务中的错误用例
    :param data: selected_node记录了错误的用例
    :return:
    """
    if data.selected_node is None or len(data.selected_node) == 0:
        return make_error_response("执行错误:没有找到错误的页面")

    task = service.find_task_by_task_id(data.group_id, data.task_id)
    plan = service.find_plan_by_id(task.plan_id)
    version = service.find_version_by_id(plan.version_id)
    page_data = service.find_selected_pages_by_selected_node(version, data.selected_node)
    if len(page_data) == 0:
        return make_error_response('执行错误:没有找到错误的页面')

    for page_data_item in page_data:
        method_data_list = []
        for d in page_data_item['method_data']:
            for method_data in d['data']:
                method_data_list.append(method_data)
        plan_data_cover_page_data(plan.data, page_data_item['data'], method_data_list)

    task.time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    task.group_id = random_id()
    task.task_id = random_id()
    task.page_data = page_data
    task.name = task.name + ":只执行错误用例"
    task.session_id = session_id
    task.wait()
    service.update_task(task)
    return make_no_data_response()


@exec_api.route("/stop_test", methods=['post'])
@model_request(TaskRequest)
def stop_test(data: TaskRequest):
    """
    前端请求停止任务
    :param data:
    :return:
    """
    task = service.find_task_by_task_id(data.group_id, data.task_id)
    task.pending_stop()
    service.update_task(task)
    return make_no_data_response()


@exec_api.route("/run_task", methods=['post'])
@model_request(TaskRequest)
def run_task(data: TaskRequest):
    """
    运行一个测试任务
    :param data:
    :return:
    """
    task = service.find_task_by_task_id(data.group_id, data.task_id)
    task.run()
    task.report_url = data.report_url
    service.update_task(task)
    return make_no_data_response()


@exec_api.route("/get_pending_stop_tasks")
def get_pending_stop_tasks():
    """
    获取预备停止的任务，前端请求停止不会马上停止，而是把任务加在这个列表中
    :return:
    """
    tasks = service.find_all_task()
    pending_stop_task = []
    for task in tasks:
        if task.is_pending_stop():
            pending_stop_task.append(task)
    return make_response(pending_stop_task)


@exec_api.route("/stop_task", methods=['post'])
@model_request(TaskRequest)
def stop_task(data: TaskRequest):
    """
    客户端报告停止一个测试
    :param data:
    :return:
    """
    task = service.find_task_by_task_id(data.group_id, data.task_id)
    if task.is_pending_stop():
        task.user_stopped()
    else:
        task.abort()
    service.update_task(task)
    return make_no_data_response()


@exec_api.route("/finished_task", methods=['post'])
@model_request(TaskRequest)
def finished_task(data: TaskRequest):
    """
    客户端报告完成测试任务
    :param data:
    :return:
    """
    task = service.find_task_by_task_id(data.group_id, data.task_id)
    if data.successful:
        task.successful()
    else:
        task.abort()
    service.update_task(task)
    return make_no_data_response()


@exec_api.route("/del_task", methods=['post'])
@model_request(TaskRequest)
def del_task(data: TaskRequest):
    """
    前端请求删除任务
    :param data:
    :return:
    """
    service.del_task(data.group_id, data.task_id)
    return make_no_data_response("删除成功")


@exec_api.route("/get_task_log", methods=['post'])
@model_request(TaskRequest)
def get_task_log(data: TaskRequest):
    """
    获取任务日志
    :param data:
    :return:
    """
    task = service.find_task_by_task_id(data.group_id, data.task_id)
    log = service.get_log_by_task(task)
    data = []
    if log is not None:
        logs = log.split('\n')
        for log in logs:
            if log is not None and len(log) > 2:
                data.append(log)
    return json.dumps(data)


@exec_api.route("/append_task_log", methods=['post'])
@model_request(TaskRequest)
def append_task_log(data: TaskRequest):
    """
    保存任务日志
    :param data:
    :return:
    """
    if data.log is None: return make_no_data_response()
    log = {'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), 'log': data.log, 'type': data.log_type}
    task = service.find_task_by_task_id(data.group_id, data.task_id)
    service.append_log_by_task(task, json.dumps(log))
    return make_no_data_response()


@exec_api.route("/get_task_step", methods=['post'])
@model_request(TaskRequest)
def get_task_step(data: TaskRequest):
    """
    获取任务步骤
    :param data:
    :return:
    """
    task = service.find_task_by_task_id(data.group_id, data.task_id)
    log = service.get_step_by_task(task)
    data = []
    if log is not None:
        logs = log.split('\n')
        for log in logs:
            if log is not None and len(log) > 2:
                data.append(log)
    return json.dumps(data)


@exec_api.route("/append_task_step", methods=['post'])
@model_request(TaskStepRequest)
def append_task_step(data: TaskStepRequest):
    """
    保存任务步骤
    :param data:
    :return:
    """
    log = data.__dict__
    log['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    task = service.find_task_by_task_id(data.group_id, data.task_id)
    service.append_step_by_task(task, json.dumps(log))
    return make_no_data_response()


@exec_api.route("/get_all_task")
@cross_origin()
def get_all_task():
    """
    获取任务列表
    :return:
    """
    tasks = service.find_all_task()
    new_task = []
    expire_task = []
    for task in reversed(tasks):
        new_task.append(task)
        if task.session_id != session_id and (task.is_pending_stop() or task.is_running()):
            task.abort()
            expire_task.append(task)

    if len(expire_task) > 0:
        service.update_tasks(expire_task)

    return make_response(new_task)


@exec_api.route('/upload_report', methods=['POST'])
def upload_report():
    """
    上传报告
    :return:
    """
    task_id = request.headers['task_id']
    group_id = request.headers['group_id']
    files = request.files
    task = service.find_task_by_task_id(group_id, task_id)
    index_html = service.save_report(task, files)
    if index_html is not None:
        task.report_url = '/static/task_report/' + task_id + "/" + index_html
        service.update_task(task)

    return make_no_data_response()


@exec_api.route("/upload_appIds", methods=['post'])
@json_request
def upload_appIds(data):
    """
    保存appid
    :param data:
    :return:
    """
    appIds = data['appIds']
    service.update_appIds(appIds)
    return make_no_data_response()


@exec_api.route("/get_appIds")
def get_appIds():
    """
    获取appid列表
    :return:
    """
    return make_response(service.find_all_appIds())
