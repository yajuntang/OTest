import logging
import base64
from library.ai_engine.visual_locator import VisualLocator


# 如果引入了 WebSocket，可以在此做实时推送
# from server.manager import socketio

class SmartDriver:
    def __init__(self, ui_driver, app_version, task_id=None):
        self.driver = ui_driver
        self.app_version = app_version
        self.task_id = task_id
        self.visual_locator = VisualLocator()

    def push_live_stream(self, action, element_name, status="success", msg=""):
        """通过 WebSocket 向前端推送实时执行状态和画面"""
        try:
            payload = {
                "task_id": self.task_id,
                "action": action,
                "element": element_name,
                "status": status,
                "message": msg,
                # 如果要做实时录播，可以把截图转 base64 传给 React 前端
                # "image": self._get_current_screen_base64()
            }
            # socketio.emit('live_execution_stream', payload, namespace='/test_exec')
            logging.info(f"[Live Stream] {action} {element_name} - {status}")
        except Exception as e:
            logging.error(f"Live stream push failed: {e}")

    def smart_click(self, element_name, locator_expr, image_template=None):
        """智能点击：原生树定位 -> 失败降级 -> AI 视觉自愈 -> 落库回传"""
        try:
            # 1. 常规执行：使用前端配置的 Poco 表达式
            logging.info(f"尝试原生点击元素: {element_name} -> {locator_expr}")
            self.driver.click(locator_expr)
            self.push_live_stream("click", element_name, "success", "原生节点点击成功")
            return True

        except Exception as e:
            logging.warning(f"前端下发的原生节点失效，触发 AI 视觉自愈: {str(e)}")

            # 2. 降级执行：调用 AI 视觉引擎进行推测
            if image_template:
                current_screen = self.driver.snapshot()
                target_coords = self.visual_locator.find_element(current_screen, image_template)

                if target_coords:
                    self.driver.click(target_coords)  # 基于推测坐标点击

                    # 3. 事件回传：通知前端平台该元素树已变更，AI代替点击了
                    healing_msg = f"⚠️ 树定位失效，已通过 AI 视觉推测坐标 {target_coords} 执行"
                    self.push_live_stream("click", element_name, "warning", healing_msg)
                    self._report_healing_to_platform(element_name, locator_expr, target_coords)
                    return True
                else:
                    error_msg = f"AI 自愈失败: 找不到元素 {element_name}"
                    self.push_live_stream("click", element_name, "error", error_msg)
                    raise Exception(error_msg)
            else:
                self.push_live_stream("click", element_name, "error", str(e))
                raise e

    def _report_healing_to_platform(self, element_name, old_expr, new_coords):
        """记录自愈事件到后端的 task_report 中，让用户在网页报告中能看到高亮提示"""
        # service.record_healing_event(self.task_id, element_name, old_expr, new_coords)
        logging.warning(f"[平台数据回传] 建议登录 OTest 更新 {element_name} 的表达式")