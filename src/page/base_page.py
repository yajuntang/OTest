from library.core.smart_driver import SmartDriver


class BasePage:
    """页面对象基类，集成智能驱动"""

    def __init__(self, poco):
        self.driver = SmartDriver(poco)

    def find_and_click(self, name, selector, anchor_img=None):
        """统一调用智能驱动的点击逻辑"""
        return self.driver.smart_click(name, selector, anchor_img)