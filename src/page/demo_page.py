from library.base.test_page import TestPage
from library.base.ui.UI import UI


class DemoPage(TestPage):
    """一个栗子🌰"""

    def __init__(self):
        self.login_button = UI(text='登录')(name='登录')
        self.username_input = UI(text='android.widget.EditText')(name='用户名')
        self.password_input = UI(text='android.widget.EditText')[1](name='密码')


    def test_login(self):
        self.login_button.wait_click()
        self.username_input.send_keys(self.username)
        self.password_input.send_keys(self.password)
        self.login_button.wait_click()
        self.login_button.wait_for_disappearance()
        self.login_button.assert_not_exists('判断登录逻辑是否成功')