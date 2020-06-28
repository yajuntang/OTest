import hashlib
import uuid
from typing import List


def md5(text):
    return hashlib.md5(text.encode(encoding='UTF-8')).hexdigest()


def random_id():
    return md5(uuid.uuid1().__str__())


class BaseModel:

    @classmethod
    def parse(cls, data):
        pass


class PageDataModel(BaseModel):

    def __init__(self, id, name, value):
        self.id = id
        self.name = name
        self.value = value

    @classmethod
    def parse(cls, data):
        return PageDataModel(data['id'], data['name'], data['value'])

    @classmethod
    def create(cls, name, value=None):
        return PageDataModel(random_id(), name, value)

    def copy(self):
        return PageDataModel.create(self.name, self.value)


class NodeModel(BaseModel):

    def __init__(self, name, alias, key, type):
        self.title = alias if alias else name
        self.name: str = name
        self.alias: str = alias
        self.key: str = key
        self.type: str = type
        self.children: List[NodeModel] = []
        self.data: List[PageDataModel] = []

    @classmethod
    def parse(cls, data):
        node = NodeModel(data['name'], data['alias'], data['key'], data['type'])
        children = node.children
        for item in data['children']:
            children.append(cls.parse(item))
        node.data = []
        for item in data['data']:
            node.data.append(PageDataModel.parse(item))
        return node


class VersionModel(BaseModel):

    def __init__(self, version_id, version_name, path, is_del=False):
        self.version_id = version_id
        self.version_name = version_name
        self.path = path
        self.is_del = is_del
        self.pages_table_name = None

    def get_pages_table_name(self):
        if self.pages_table_name is None:
            self.pages_table_name = hashlib.md5(self.version_id.encode(encoding='UTF-8')).hexdigest()
        return self.pages_table_name

    @classmethod
    def parse(cls, data):
        version = VersionModel(None, None, None)
        version.__dict__ = data
        return version

    @classmethod
    def create(cls, version_name, path):
        return VersionModel(random_id(), version_name, path)


class PlanModel(BaseModel):

    def __init__(self, plan_id, name, version_id, parent_id):
        self.plan_id = plan_id
        self.parent_id = parent_id
        self.name = name
        self.version_id = version_id
        self.children: List[PlanModel] = []
        self.selected_page_node: List[str] = []
        self.data: List[PageDataModel] = []

    @classmethod
    def parse(cls, data):
        plan = PlanModel(data['plan_id'], data['name'], data['version_id'], None)

        if 'parent_id' in data:
            plan.parent_id = data['parent_id']

        children = plan.children
        for item in data['children']:
            children.append(cls.parse(item))
        plan.selected_page_node = data['selected_page_node']

        plan.data = []
        for item in data['data']:
            plan.data.append(PageDataModel.parse(item))

        return plan

    @classmethod
    def create(cls, name, version_id, parent_id):
        return PlanModel(random_id(), name, version_id, parent_id)
