# src/page/demo_page.py
import logging
from src.page.base_page import BasePage


class DemoPage(BasePage):
    """
    演示页面对象：采用组件化封装与 AI 视觉对冲机制。
    [专家视点]：将选择器（Selector）与业务动作分离，确保高可维护性。
    """

    # 1. 元素定义区 (与逻辑分离，方便后期维护)
    SELECTORS = {
        "login_btn": {"name": "com.example:id/login_button"},
        "username_field": {"text": "请输入用户名"},
        "password_field": {"type": "PasswordField"},
        "avatar": {"name": "user_avatar"}
    }

    # 2. 视觉锚点区 (用于 AI 自愈识别)
    ANCHOR_IMAGES = {
        "login_btn": "res/anchors/login_btn_gold.png",
        "avatar": "res/anchors/default_avatar.png"
    }

    def login(self, username, password):
        """
        标准登录流程：展示原生定位与 AI 自愈的结合。
        """
        logging.info(f"🚀 开始登录流程，用户: {username}")

        # 使用 SmartDriver 进行智能输入（可后续扩展 smart_set_text）
        self.driver.poco(**self.SELECTORS["username_field"]).set_text(username)
        self.driver.poco(**self.SELECTORS["password_field"]).set_text(password)

        # 核心：调用带 AI 自愈能力的智能点击
        # 如果 login_btn 的 ID 变了，SmartDriver 会自动根据 anchor_img 找回。
        success = self.find_and_click(
            name="登录按钮",
            selector=self.SELECTORS["login_btn"],
            anchor_img=self.ANCHOR_IMAGES["login_btn"]
        )

        if success:
            logging.info("✅ 登录动作已触发")
        return success

    def check_login_status(self):
        """验证登录是否成功，利用视觉锚点进行双重校验"""
        return self.driver.smart_click(
            name="用户头像",
            selector=self.SELECTORS["avatar"],
            anchor_img=self.ANCHOR_IMAGES["avatar"]
        )