from src.page.base_page import PlatformBasePage

class LoginPage(PlatformBasePage):
    def __init__(self, driver, app_version):
        super().__init__(driver, page_name="login_page", app_version=app_version)

    def do_login(self, username, password):
        # 此时代码彻底告别了杂乱的 Locator 配置，所有定位依赖 Web 平台
        self.input_text('username_input', username)
        self.input_text('password_input', password)
        self.platform_click('login_button')