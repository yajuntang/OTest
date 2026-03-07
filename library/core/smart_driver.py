import logging
from library.ai_engine.visual_locator import VisualLocator
from library.ai_engine.token_manager import TokenManager


class SmartDriver:
    """
    10年资深老兵实战封装：UI 自动化智能驱动层
    实现核心：原生 Poco 失败后，自动启动 AI 视觉对冲 (Hedging) 逻辑。
    """

    def __init__(self, poco_instance):
        self.poco = poco_instance
        self.tm = TokenManager()
        self.vl = VisualLocator()

    def smart_click(self, name, selector, anchor_img=None, timeout=10):
        """带有自愈能力的智能点击"""
        try:
            # 1. 优先尝试原生定位
            element = self.poco(**selector).wait(timeout)
            if element.exists():
                element.click()
                logging.info(f"✅ [{name}] 元素定位成功并点击")
                return True
            raise Exception("Poco element not found")

        except Exception as e:
            logging.warning(f"⚠️ [{name}] 原生定位失效: {e}，尝试 AI 智能自愈...")

            # 2. 检查 Token 预算并启动 AI 视觉
            if self.tm.can_consume():
                # 先尝试 OpenCV (零成本)，再尝试 LLM (高精度)
                pos = self.vl.find_by_opencv(anchor_img) or self.vl.find_by_llm(name)

                if pos:
                    self.poco.click(pos)
                    self.tm.record_usage(500)  # 记录成本
                    logging.info(f"🔥 [{name}] AI 自愈成功，点击位置: {pos}")
                    return True

            logging.error(f"❌ [{name}] 彻底定位失败，触发质量预警。")
            return False