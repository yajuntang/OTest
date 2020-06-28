from flask import Blueprint
from flask_cors import cross_origin

from server.app.database.service import service
from server.app.models.models import PlanModel, random_id
from server.app.models.request_models import PlanHandleRequest
from server.app.utils import make_no_data_response, make_error_response, model_request, make_response

plan_api = Blueprint("plan_api", __name__)


@plan_api.route("/get_plans")
@cross_origin()
def get_plans():
    plans = service.find_all_plan()
    return make_response(plans)


@plan_api.route("/add_plan", methods=['post'])
@model_request(cls=PlanHandleRequest)
def add_plan(data: PlanHandleRequest):
    version = service.find_version_by_id(data.version_id)
    if version is None:
        return make_error_response("版本错误")

    plan = PlanModel.create(data.name, data.version_id, data.parent_id)

    if data.parent_id is not None:
        parent_plan = service.find_plan_by_id(data.parent_id)
        if parent_plan is not None:
            plan.selected_page_node = parent_plan.selected_page_node
            for plan_data in parent_plan.data:
                plan.data.append(plan_data.copy())
    service.update_plan(plan)

    return make_no_data_response("创建成功")


@plan_api.route("/copy_plan", methods=['post'])
@model_request(cls=PlanHandleRequest)
def copy_plan(data: PlanHandleRequest):
    plan: PlanModel = service.find_plan_by_id(data.plan_id)

    if data.version_id is None and plan.parent_id is not None:
        parent_plan = service.find_plan_by_id(plan.parent_id)
        data.version_id = parent_plan.version_id

    version = service.find_version_by_id(data.version_id)
    if version is None:
        return make_error_response("版本错误")

    def set_id(p: PlanModel, parent_id):
        p.plan_id = random_id()
        p.version_id = version.version_id
        p.parent_id = parent_id
        for item in p.children:
            set_id(item, p.plan_id)

    set_id(plan, plan.parent_id)
    plan.name = data.name
    plan.version_id = version.version_id
    service.update_plan(plan)
    return make_no_data_response("创建成功")


@plan_api.route("/del_plan", methods=['post'])
@model_request(cls=PlanHandleRequest)
def del_plan(data: PlanHandleRequest):
    plan = service.find_plan_by_id(data.plan_id)
    service.del_plan(plan)
    if plan.parent_id is  None:
        version = service.find_version_by_id(data.version_id,include_del=True)
        if version is not None and version.is_del:
            service.del_pages_versions(version)
            service.del_pages_info(version)

    return make_no_data_response("删除成功")


@plan_api.route("/update_selected_page_node", methods=['post'])
@model_request(cls=PlanHandleRequest)
def update_selected_page_node(data: PlanHandleRequest):
    names = [item for item in map(lambda item: item.name, data.data)]

    set_name = set(names)
    if len(set_name) != len(names):
        return make_error_response("不可以重复添加变量名")

    plan = service.find_plan_by_id(data.plan_id)

    if plan is None:
        return make_error_response("没有找到该计划")

    plan.selected_page_node = data.selected_page_node
    service.update_plan(plan)
    return make_no_data_response()


@plan_api.route("/save_plan_data", methods=['post'])
@model_request(cls=PlanHandleRequest)
def save_plan_data(data: PlanHandleRequest):
    names = [item for item in map(lambda item: item.name, data.data)]

    set_name = set(names)
    if len(set_name) != len(names):
        return make_error_response("不可以重复添加变量名")

    plan = service.find_plan_by_id(data.plan_id)

    if plan is None:
        return make_error_response("没有找到该计划")

    plan.data = data.data
    service.update_plan(plan)
    return make_no_data_response()


@plan_api.route("/del_plan_data", methods=['post'])
@model_request(cls=PlanHandleRequest)
def del_plan_data(data: PlanHandleRequest):
    plan = service.find_plan_by_id(data.plan_id)

    if plan is None:
        return make_error_response("没有找到该计划")

    pending_del_id = [item for item in map(lambda item: item.id, data.data)]

    new_data = [item for item in filter(lambda item: item.id not in pending_del_id, plan.data)]
    plan.data = new_data
    service.update_plan(plan)
    return make_no_data_response()
