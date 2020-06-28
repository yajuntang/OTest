from flask import Blueprint

from server.app.database.service import service
from server.app.models.request_models import SavePageDataRequest
from server.app.utils import find_node_by_key, make_no_data_response, make_error_response, model_request

pages_api = Blueprint("pages_api", __name__)


@pages_api.route("/save_page_data", methods=['post'])
@model_request(cls=SavePageDataRequest)
def save_page_data(data: SavePageDataRequest):

    names = [item for item in map(lambda item: item.name, data.data)]

    set_name = set(names)
    if len(set_name) != len(names):
        return make_error_response("不可以重复添加变量名")


    version = service.find_version_by_id(data.version_id)
    if version is None:
        return make_error_response("版本错误")

    page_info = service.find_pages_info(version)
    node = find_node_by_key(page_info, data.node_key)

    if node is None:
        return make_error_response("没有找到该节点信息")


    node.data = data.data
    service.save_pages_info(version, page_info)
    return make_no_data_response()


@pages_api.route("/del_page_data", methods=['post'])
@model_request(cls=SavePageDataRequest)
def del_page_data(data: SavePageDataRequest):
    version = service.find_version_by_id(data.version_id)
    if version is None:
        return make_error_response("版本错误")

    page_info = service.find_pages_info(version)
    node = find_node_by_key(page_info, data.node_key)

    if node is None:
        return make_error_response("没有找到该节点信息")
    pending_del_id = [item for item in map(lambda item: item.id, data.data)]

    new_data = [item for item in filter(lambda item: item.id not in pending_del_id, node.data)]
    node.data = new_data
    if service.save_pages_info(version, page_info):
        return make_no_data_response("删除成功")
    else:
        return make_no_data_response("删除失败")

