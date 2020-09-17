import os

from werkzeug.datastructures import FileStorage

from library.client.Task import Task
from server.app.database.database import DataBase
from server.app.models.models import VersionModel, NodeModel, PlanModel
from server.app.utils import dir_modules, plans_flat_to_dict
from typing import List, Dict

url = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")

report_url = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static"),
                          'task_report')

version_pages_table_name = "pages_version.data"

plan_table_name = "plan.data"
task_table_name = "task.data"
task_db_name = "tasks"
default_db_name = ''


class Service:
    def __init__(self):
        """
        初始化数据库
        """
        self.__db = DataBase(url)

    def update_pages_version_info(self, version: VersionModel):
        """
        更新页面版本信息到数据库
        :param version:
        :return:
        """
        versions = self.find_all_version_pages()
        new_versions = []
        for item in versions:
            if item.version_id == version.version_id:
                new_versions.append(version)
            else:
                new_versions.append(item)

        if version not in new_versions:
            new_versions.append(version)

        self.__db.save_to_db(default_db_name, version_pages_table_name, new_versions)

    def del_pages_versions(self, version: VersionModel):
        """
        从数据中删除页面版本信息
        :param version:
        :return:
        """
        versions = self.find_all_version_pages()
        new_versions = []
        for item in versions:
            if item.version_id != version.version_id:
                new_versions.append(item)
        self.__db.save_to_db(default_db_name, version_pages_table_name, new_versions)

    def del_pages_info(self, version: VersionModel):
        """
        删除页面信息
        :param version:
        :return:
        """
        self.__db.drop_table(default_db_name, version.pages_table_name)

    def find_all_version_pages(self, include_del=True) -> List[VersionModel]:
        """
        查找所有的版本列表
        :param include_del:
        :return:
        """
        versions = []
        versions_data = self.__db.find_from_db_and_cover_json(default_db_name, version_pages_table_name, [])
        for item in versions_data:
            version = VersionModel.parse(item)
            if include_del:
                versions.append(version)
            elif not version.is_del:
                versions.append(version)
        return versions

    def find_version_by_id(self, version_id, include_del=False) -> VersionModel:
        """
        通过id查询版本信息
        :param version_id:
        :param include_del:
        :return:
        """
        versions = self.find_all_version_pages(include_del)
        for item in versions:
            if item.version_id == version_id:
                return item

    def parse_pages_info_and_save(self, version: VersionModel) -> bool:
        """
        解析页面数据并保存
        :param version:
        :return:
        """
        try:
            pages_data = dir_modules(version.path)
        except:
            return False
        return self.save_pages_info(version, pages_data)

    def save_pages_info(self, version: VersionModel, pages_data: List[NodeModel]) -> bool:
        """
        保存页面信息
        :param version:
        :param pages_data:
        :return:
        """
        if pages_data.__len__() == 0:
            return False
        self.__db.save_to_db(default_db_name, version.get_pages_table_name(), pages_data)
        return True

    def find_pages_info(self, version: VersionModel) -> List[NodeModel]:
        """
        查找页面信息
        :param version:
        :return:
        """
        pages_data = []
        pages_data_dict = self.__db.find_from_db_and_cover_json(default_db_name, version.get_pages_table_name(), [])

        for item in pages_data_dict:
            pages_data.append(NodeModel.parse(item))

        return pages_data

    def update_plan(self, plan: PlanModel):
        """
        更新测试计划
        :param plan:
        :return:
        """
        plans = self.find_all_plan()
        temp_plans = plans
        new_plans = []
        parent_node: PlanModel = None

        if plan.parent_id is not None:
            plans_dict = plans_flat_to_dict(plans)
            if plan.parent_id in plans_dict:
                parent_node = plans_dict[plan.parent_id]
                temp_plans = parent_node.children
            else:
                plan.parent_id = None

        for item in temp_plans:
            if item.plan_id == plan.plan_id:
                new_plans.append(plan)
            else:
                new_plans.append(item)

        if plan not in new_plans:
            new_plans.append(plan)

        if parent_node is not None:
            parent_node.children = new_plans
        else:
            plans = new_plans

        self.__db.save_to_db(default_db_name, plan_table_name, plans)

    def del_plan(self, plan: PlanModel):
        """
        删除测试计划
        :param plan:
        :return:
        """
        plans = self.find_all_plan()
        temp_plans = []

        def list_plans(old_plans, new_plans):
            for item in old_plans:
                if item.plan_id != plan.plan_id:
                    new_plans.append(item)
                if len(item.children) > 0:
                    new_children = []
                    list_plans(item.children, new_children)
                    item.children = new_children

        list_plans(plans, temp_plans)

        self.__db.save_to_db(default_db_name, plan_table_name, temp_plans)

    def find_plan_by_id(self, plan_id) -> PlanModel:
        """
        通过id查找即测试计划
        :param plan_id:
        :return:
        """
        plans = self.find_all_plan()
        plans_dict = plans_flat_to_dict(plans)
        if plan_id in plans_dict:
            return plans_dict[plan_id]

    def find_all_plan(self) -> List[PlanModel]:
        """
        查找所有的测试计划
        :return:
        """
        plans = []
        plan_data = self.__db.find_from_db_and_cover_json(default_db_name, plan_table_name, [])
        for item in plan_data:
            plans.append(PlanModel.parse(item))
        return plans

    def find_selected_pages_by_plan(self, plan):
        """
        查找指定测试计划的选择的页面
        :param plan:
        :return:
        """
        version = self.find_version_by_id(plan.version_id)
        selected_node = plan.selected_page_node
        return self.find_selected_pages_by_selected_node(version, selected_node)

    def find_selected_pages_by_selected_node(self, version, selected_node):
        """
        通过节点查找选择的页面
        :param version:
        :param selected_node:
        :return:
        """
        if len(selected_node) == 0: return []
        new_pages = []
        pages = self.find_pages_info(version)
        dict_pages = {}

        def flat_pages_to_dict(pages: List[NodeModel]):
            for item in pages:
                if item.type == "class" or item.type == 'method':
                    dict_pages[item.key] = item
                if len(item.children) > 0:
                    flat_pages_to_dict(item.children)

        flat_pages_to_dict(pages)

        dict_classes = {}

        for item in selected_node:
            if item not in dict_pages:
                continue
            node = dict_pages[item]
            if node.type == "class":
                if node.key in dict_classes:
                    continue
                classes = {'path': node.key, 'name': node.name, 'alias': node.alias, 'data': node.data,
                           'method_data': []}
                new_pages.append(classes)
                dict_classes[node.key] = classes
            elif node.type == 'method':
                parent_key = node.key.replace('.' + node.name, "")
                if parent_key in dict_classes:
                    classes = dict_classes[parent_key]
                else:
                    parent = dict_pages[parent_key]
                    classes = {'path': parent.key, 'name': parent.name, 'alias': parent.alias, 'data': parent.data,
                               'method_data': []}
                    new_pages.append(classes)
                    dict_classes[parent_key] = classes
                classes['method_data'].append({'path': node.key, 'data': node.data, 'name': node.name})

        return new_pages

    def get_test_plans(self, plan_id) -> List[PlanModel]:
        """
        获取测试计划
        :param plan_id:
        :return:
        """
        test_plans = []
        plan = self.find_plan_by_id(plan_id)

        def get_terminal_plan(p: PlanModel):
            if len(p.children) == 0:
                test_plans.append(p)
            else:
                for item in p.children:
                    get_terminal_plan(item)

        if plan is not None:
            get_terminal_plan(plan)

        return test_plans

    def find_task_group_by_group_id(self, group_id) -> List[Task]:
        """
        查找任务组通过任务组id
        :param group_id:
        :return:
        """
        group_task_obj = []
        group_task = self.__db.find_from_db_and_cover_json(task_db_name, group_id, [])
        for item in group_task:
            group_task_obj.append(Task.parse(item))
        return group_task_obj

    def find_all_task(self) -> List[Task]:
        """
        查找所有的任务
        :return:
        """
        tasks = []
        tasks_groups = self.__db.find_from_db_and_cover_json(task_db_name, task_table_name, [])
        for group_id in tasks_groups:
            group_task = self.find_task_group_by_group_id(group_id)
            tasks += group_task
        return tasks

    def find_all_group(self) -> List[str]:
        """
        查找所有的任务组
        :return:
        """
        tasks_groups = self.__db.find_from_db_and_cover_json(task_db_name, task_table_name, [])
        return tasks_groups

    def update_task_groups(self, group_ids):
        """
        更新任务组
        :param group_ids:
        :return:
        """
        tasks_groups = self.__db.find_from_db_and_cover_json(task_db_name, task_table_name, [])
        for group_id in group_ids:
            if group_id not in tasks_groups:
                tasks_groups.append(group_id)
        self.__db.save_to_db(task_db_name, task_table_name, tasks_groups)

    def remove_task_groups(self, group_ids):
        """
        移除整个任务组
        :param group_ids:
        :return:
        """
        tasks_groups = self.__db.find_from_db_and_cover_json(task_db_name, task_table_name, [])
        for group_id in tasks_groups[:]:
            if group_id in group_ids:
                tasks_groups.remove(group_id)
        self.__db.save_to_db(task_db_name, task_table_name, tasks_groups)

    def update_task(self, update_task: Task):
        """
        更新某个任务
        :param update_task:
        :return:
        """
        group_task = self.find_task_group_by_group_id(update_task.group_id)

        for item in group_task:
            if item.task_id == update_task.task_id:
                group_task.remove(item)
                group_task.append(update_task)
                break

        if update_task not in group_task:
            group_task.append(update_task)

        self.__db.save_to_db(task_db_name, update_task.group_id, group_task)
        self.update_task_groups([update_task.group_id])

    def update_tasks(self, update_tasks: List[Task]):
        """
        更新一批任务
        :param update_tasks:
        :return:
        """
        group_ids = set()

        for update_task in update_tasks:
            group_id = update_task.group_id
            group_ids.add(group_id)
            group_task = self.find_task_group_by_group_id(group_id)
            for item in group_task:
                if item.task_id == update_task.task_id:
                    group_task.remove(item)
                    group_task.append(update_task)
                    break

            if update_task not in group_task:
                group_task.append(update_task)
            self.__db.save_to_db(task_db_name, group_id, group_task)

        self.update_task_groups(group_ids)

    def del_task(self, group_id, task_id):
        """
        删除某个任务
        :param group_id:
        :param task_id:
        :return:
        """
        group_task = self.find_task_group_by_group_id(group_id)
        del_task = None
        for task in group_task:
            if task.task_id == task_id:
                del_task = task

        if del_task is not None:
            group_task.remove(del_task)
            self.__db.drop_table(task_db_name, del_task.get_step_table_name())
            self.__db.drop_table(task_db_name, del_task.get_log_table_name())

        if len(group_task) == 0:
            self.__db.drop_table(task_db_name, group_id)
            self.remove_task_groups([group_id])
        else:
            self.__db.save_to_db(task_db_name, group_id, group_task)

    def find_task_by_task_id(self, group_id, task_id):
        """
        查找某个任务 通过任务id
        :param group_id:
        :param task_id:
        :return:
        """
        group_task = self.find_task_group_by_group_id(group_id)
        for item in group_task:
            if item.task_id == task_id: return item

    def get_log_by_task(self, task: Task):
        """
        获取该任务的日志
        :param task:
        :return:
        """
        log = self.__db.find(task_db_name, task.get_log_table_name(), None)
        return log

    def append_log_by_task(self, task: Task, log):
        """
        追加该任务的日志
        :param task:
        :param log:
        :return:
        """
        self.__db.append(task_db_name, task.get_log_table_name(), log + "\n")

    def get_step_by_task(self, task: Task):
        """
        获取该任务的测试步骤
        :param task:
        :return:
        """
        log = self.__db.find(task_db_name, task.get_step_table_name(), None)
        return log

    def append_step_by_task(self, task: Task, log):
        """
        追加该任务的测试步骤
        :param task:
        :param log:
        :return:
        """
        self.__db.append(task_db_name, task.get_step_table_name(), log + "\n")

    def save_report(self, task, files: Dict[str, FileStorage]):
        """
        保存报告
        :param task:
        :param files:
        :return:
        """
        table = os.path.join(report_url, task.task_id)
        if not os.path.exists(table):
            os.makedirs(table, exist_ok=True)

        index_html = None

        for key in files:
            dir_name = os.path.dirname(key)
            file_dir = os.path.join(table, dir_name)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir, exist_ok=True)

            if key.endswith('.html'):
                index_html = key
                data = files[key].stream.read()
                content = bytes.decode(data)
                content = content.replace('Airtest Report', task.name)
                with open(os.path.join(table, key), 'w+') as f:
                    f.write(content)
                    f.close()
            else:
                files[key].save(os.path.join(table, key))
        return index_html

    def update_appIds(self, appIds: List[str]):
        """
        保存appid列表
        :param appIds:
        :return:
        """
        self.__db.save_to_db(default_db_name, 'appIds.data', appIds)

    def find_all_appIds(self):
        """
        查找所有的appid
        :return:
        """
        return self.__db.find_from_db_and_cover_json(default_db_name, 'appIds.data', [])


service = Service()
