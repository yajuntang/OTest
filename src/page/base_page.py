import logging
from library.core.smart_driver import SmartDriver
# 引入后端的服务层，用于实时读取前端(pages_version.data)中配置的控件数据
from server.app.database.service import service


class PlatformBasePage:
    def __init__(self, driver: SmartDriver, page_name: str, app_version: str):
        """
        :param driver: 包装后的智能驱动 SmartDriver
        :param page_name: 对应前端 Web 页面上配置的 "页面名称"
        :param app_version: 对应前端配置的 App 版本号
        """
        self.driver = driver
        self.page_name = page_name
        self.app_version = app_version

    def _get_node_from_platform(self, element_key):
        """直接从 OTest 平台存储中实时拉取最新的节点配置"""
        try:
            # 根据真实后端的 service.py 读取数据的逻辑进行调用
            version_data = service.get_version_data(self.app_version)
            if not version_data:
                raise ValueError(f"未找到版本 {self.app_version} 的配置数据")

            page_data = version_data.get_page(self.page_name)
            node = page_data.get_node(element_key)
            return node
        except Exception as e:
            logging.error(f"无法从平台拉取控件数据 [{self.page_name} -> {element_key}]: {e}")
            raise

    def platform_click(self, element_key):
        """完全由前端数据驱动的智能点击"""
        # 1. 实时拉取前端维护的属性
        node = self._get_node_from_platform(element_key)

        # 2. 从平台数据中提取表达式与特征图
        locator_expr = node.get('expr')  # 前端填写的 poco("xxx")
        image_template = node.get('image_path')  # 前端绑定的备用特征截图

        # 3. 传给智能驱动器执行 (附带自愈能力)
        self.driver.smart_click(
            element_name=f"{self.page_name}_{element_key}",
            locator_expr=locator_expr,
            image_template=image_template
        )