import importlib
import inspect
import json
import os
import sys
import re
from functools import wraps
from typing import List, Dict

from flask import make_response as response, request

from library.base.test_page import TestPage
from server.app.models.models import NodeModel, PlanModel, PageDataModel


class ObjJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if not isinstance(o, (list, dict)):
            return o.__dict__


def make_response(data, code=1):
    return response(obj_to_json({'code': code, 'data': data}))


def make_response_not_to_json(data):
    return response(data)


def make_no_data_response(desc=None, code=1):
    return response(obj_to_json({'code': code, 'desc': desc}))


def make_error_response(desc=None, code=-1):
    return response(obj_to_json({'code': code, 'desc': desc}))


def obj_to_json(obj):
    return json.dumps(obj, cls=ObjJSONEncoder)


def node_info(name, alias, key, type):
    return NodeModel(name, alias, key, type)


def get_module_path(m):
    path = m.__path__
    if isinstance(path, list):
        return path[0]
    else:
        return m.__path__._path[0]


def dir_modules(path):
    modules = []
    parse_modules(path, modules)

    def remove_no_test_method_class(node, parent_list: List[NodeModel]):
        if node.type == 'class':
            if len(node.children) == 0:
                parent_list.remove(node)
            return
        if len(node.children) > 0:
            for child in node.children[:]:
                remove_no_test_method_class(child, node.children)

        if len(node.children) == 0:
            parent_list.remove(node)

    for module in modules[:]:
        remove_no_test_method_class(module, modules)
    return modules


def parse_modules(path, modules):
    m = importlib.import_module(path.replace("/", "."))
    dirs = [item for item in os.listdir(get_module_path(m)) if
            item not in ("__pycache__", "__init__.py")]
    packages = []
    py_files = []
    for name in dirs:  # 文件夹和文件分开处理
        if name.endswith(".py"):
            py_files.append(name)
        else:
            packages.append(name)

    packages.sort()
    py_files.sort()
    for name in packages:
        try:
            module_path = os.path.join(path, name).replace("/", ".")
            m = importlib.import_module(module_path)
            # node = node_info(name, m.__doc__, module_path, "package")
            # modules.append(node)
            parse_modules(module_path, modules)
        except ModuleNotFoundError:
            continue

    for name in py_files:
        name = name.replace(".py", "")
        py_files_path = os.path.join(path, name).replace("/", ".")
        try:
            m = importlib.import_module(py_files_path)
            # node = node_info(name, m.__doc__, py_files_path, "module")
            # modules.append(node)
            class_children = modules
            for name, obj in inspect.getmembers(sys.modules[m.__name__]):
                if inspect.isclass(obj) and TestPage in inspect.getmro(obj):
                    if obj.__module__ == py_files_path:
                        test_methods_name = [m for m in obj.__dict__ if m.startswith("test")]
                        class_key = py_files_path + "." + obj.__name__
                        node = node_info(obj.__name__, obj.__doc__, class_key, "class")
                        class_children.append(node)
                        test_methods_children = node.children
                        for method_name in test_methods_name:
                            node = node_info(method_name, None, class_key + "." + method_name, "method")
                            test_methods_children.append(node)
                            method = getattr(obj, method_name)
                            args = [*inspect.getfullargspec(method).args]
                            if len(args) > 0:
                                args.pop(0)
                                for arg in args:
                                    node.data.append(PageDataModel.create(arg))
        except Exception as e:
            print(e)
            continue


def model_request(cls):
    def wrap1(f):
        @wraps(f)
        def wrap2():
            data = request.get_data()
            json_data = json.loads(data.decode("utf-8"))
            print(json_data)
            json_data = cls.parse(json_data)
            return f(json_data)

        return wrap2

    return wrap1


def json_request(f):
    @wraps(f)
    def wrap2():
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        print(json_data)
        return f(json_data)

    return wrap2


def find_node_by_key(nodes: List[NodeModel], key: str) -> NodeModel:
    for item in nodes:
        if item.key == key:
            return item

    for item in nodes:
        node = find_node_by_key(item.children, key)
        if node is not None:
            return node


def replace_pages_data(old_pages: List[NodeModel], new_pages: List[NodeModel]):
    old_data = {}

    def get_method_key(node: NodeModel):
        return re.compile('.*\.').sub('', node.key) + "." + node.name

    def data_flat_to_dict(node: NodeModel):
        if len(node.data) > 0:
            if node.type == 'class':
                old_data[node.name] = node.data
            elif node.type == 'method':
                old_data[get_method_key(node)] = node.data

        if len(node.children) > 0:
            for child in node.children:
                data_flat_to_dict(child)

    for item in old_pages:
        data_flat_to_dict(item)

    def iter_new_pages(node: NodeModel):

        if node.type == 'class':
            if node.name in old_data:
                node.data = old_data[node.name]
        elif node.type == 'method':
            if get_method_key(node) in old_data:
                node.data = old_data[get_method_key(node)]

        if len(node.children) > 0:
            for child in node.children:
                iter_new_pages(child)

    for item in new_pages:
        iter_new_pages(item)


def plans_flat_to_dict(data: List[PlanModel]) -> Dict[str, PlanModel]:
    data_dict = {}

    def data_flat_to_dict(plan: PlanModel):
        data_dict[plan.plan_id] = plan

        if len(plan.children) > 0:
            for child in plan.children:
                data_flat_to_dict(child)

    for item in data:
        data_flat_to_dict(item)

    return data_dict


def plan_data_cover_page_data(plan_data: List[PageDataModel], page_data: List[PageDataModel],
                              method_data: List[PageDataModel]):
    if plan_data is None: return

    def find_page_data_models_by_name(data: List[PageDataModel], name, items):
        if data is None: return
        for item in data:
            if item.name == name:
                items.append(item)

    not_found_items = []

    for plan_data_item in plan_data:
        class_data_items = []
        method_data_items = []
        find_page_data_models_by_name(page_data, plan_data_item.name, class_data_items)
        find_page_data_models_by_name(method_data, plan_data_item.name, method_data_items)

        for data_item in class_data_items:
            data_item.value = plan_data_item.value

        for data_item in method_data_items:
            data_item.value = plan_data_item.value

        if len(class_data_items) == 0 and len(method_data_items) == 0:
            not_found_items.append(plan_data_item)

    if len(not_found_items) > 0:
        for plan_data_item in not_found_items:
            page_data.append(plan_data_item)
