from typing import List

from server.app.models.models import BaseModel, PageDataModel, VersionModel, PlanModel


class SavePageDataRequest(BaseModel):

    def __init__(self, version_id, node_key, data: List[PageDataModel]):
        self.version_id = version_id
        self.node_key = node_key
        self.data = data

    @classmethod
    def parse(cls, data):
        save_page_data_model = SavePageDataRequest(data['version_id'], data['node_key'], [])
        for item in data['data']:
            save_page_data_model.data.append(PageDataModel.parse(item))
        return save_page_data_model


class VersionHandleRequest(VersionModel):

    @classmethod
    def parse(cls, data):
        version = VersionModel(None, None, None, None)
        version.__dict__ = data
        version.pages_table_name = None
        return version


class PlanHandleRequest(PlanModel):

    @classmethod
    def parse(cls, data):
        plan = PlanHandleRequest(None, None, None, None)

        plan.__dict__ = data
        if 'parent_id' in data:
            plan.parent_id = data['parent_id']
        else:
            plan.parent_id = None

        if 'version_id' in data:
            plan.version_id = data['version_id']
        else:
            plan.version_id = None

        plan_data = []
        if 'data' in data:
            for item in data['data']:
                plan_data.append(PageDataModel.parse(item))
        plan.data = plan_data
        return plan


class StartTestRequest(BaseModel):

    def __init__(self, plan_id=None, platform=None, ip=None, port=None, device_id=None,app_id=None):
        self.platform = platform
        self.plan_id = plan_id
        self.type = type
        self.ip = ip
        self.port = port
        self.app_id = app_id
        self.device_id = device_id

    @classmethod
    def parse(cls, data):
        return StartTestRequest(**data)


class TaskRequest(BaseModel):

    def __init__(self, group_id, task_id, successful=False, log=None, log_type=None, report_url=None,
                 selected_node=None):
        self.task_id = task_id
        self.group_id = group_id
        self.log = log
        self.successful = successful
        self.log_type = log_type
        self.report_url = report_url
        self.selected_node = selected_node

    @classmethod
    def parse(cls, data):
        return TaskRequest(**data)


class TaskStepRequest(BaseModel):

    def __init__(self, group_id, task_id, title, sub_title, message=None, attach=None, successful=False):
        self.task_id = task_id
        self.group_id = group_id
        self.title = title
        self.sub_title = sub_title
        self.message = message
        self.attach = attach
        self.successful = successful

    @classmethod
    def parse(cls, data):
        return TaskStepRequest(**data)
