from flask import Blueprint
from flask_cors import cross_origin

from server.app.database.service import service
from server.app.models.models import VersionModel, PlanModel
from server.app.models.request_models import VersionHandleRequest
from server.app.utils import make_no_data_response, make_error_response, make_response, model_request, dir_modules, \
    replace_pages_data

pages_version_api = Blueprint('pages_version_api', __name__)


@pages_version_api.route("/get_version_pages")
@cross_origin()
def get_version_pages():
    """
    获取版本列表
    :return:
    """
    versions = service.find_all_version_pages(include_del=False)
    pages = []
    for item in versions:
        pages.append({
            'version_id': item.version_id,
            "name": item.version_name,
            "path": item.path,
            "pages": service.find_pages_info(item)
        })
    return make_response(pages)

@pages_version_api.route("/get_plan_version_pages")
@cross_origin()
def get_plan_version_pages():
    """
    获取版本计划列表 包括删除的
    :return:
    """
    versions = service.find_all_version_pages(include_del=True)
    pages = []
    for item in versions:
        pages.append({
            'version_id': item.version_id,
            "name": item.version_name,
            "path": item.path,
            "pages": service.find_pages_info(item)
        })
    return make_response(pages)


@pages_version_api.route("/add_version", methods=['post'])
@model_request(cls=VersionHandleRequest)
def add_version(data: VersionHandleRequest):
    """
    添加版本
    :param data:
    :return:
    """
    version = VersionModel.create(data.version_name, data.path)
    if not service.parse_pages_info_and_save(version):
        return make_error_response("添加失败,请检查你的代码路径(path)")
    service.update_pages_version_info(version)
    return make_no_data_response("添加成功")


@pages_version_api.route("/copy_version", methods=['post'])
@model_request(cls=VersionHandleRequest)
def copy_version(data: VersionHandleRequest):
    """
    复制一个版本
    :param data:
    :return:
    """
    version = VersionModel.create(data.version_name, data.path)
    pages_data = []
    try:
        pages_data = dir_modules(version.path)
    except:
        pass

    if len(pages_data) == 0:
        return make_error_response("添加失败,请检查你的代码路径(path)")

    old_pages_data = service.find_pages_info(data)
    replace_pages_data(old_pages_data, pages_data)
    service.save_pages_info(version, pages_data)
    service.update_pages_version_info(version)
    return make_no_data_response("添加成功")


@pages_version_api.route("/del_version", methods=['post'])
@model_request(cls=VersionHandleRequest)
def del_version(data: VersionHandleRequest):
    """
    删除版本
    :param data:
    :return:
    """
    version = service.find_version_by_id(data.version_id)
    if version is None:
        return make_error_response("版本错误")

    used = False
    plans = service.find_all_plan()

    def check_plan_version(plan:PlanModel):
        if plan.version_id == version.version_id:
            return True
        if plan.children.__len__() > 0:
            for child in plan.children:
               result = check_plan_version(child)
               if result:
                   return True

    for item in plans:
        used = check_plan_version(item)
        if used:
            break
    if used:
        version.is_del = True
        service.update_pages_version_info(version)
    else:
        service.del_pages_versions(version)
        service.del_pages_info(version)

    return make_no_data_response("删除成功")
