# main.py
import logging
from airtest.core.api import connect_device, auto_setup
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
from src.page.demo_page import DemoPage

# 配置日志：展现资深老兵对调试信息的掌控
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run_test():
    """自动化测试主入口"""
    logging.info("🚀 正在初始化自动化测试环境...")

    # 1. 连接设备（建议参数化，方便后期接入云真机平台）
    auto_setup(__file__)
    device = connect_device("Android:///")
    poco = AndroidUiautomationPoco(device)

    # 2. 业务链路执行
    try:
        demo = DemoPage(poco)

        # 演示：执行带 AI 自愈的登录流程
        if demo.login("yajun_tang", "pwd123456"):
            logging.info("🎯 测试任务圆满完成！")
        else:
            logging.error("❌ 测试任务因定位失效中断，请复盘 AI 自愈日志。")

    except Exception as e:
        logging.critical(f"💥 运行过程中发生未捕获异常: {e}")


if __name__ == "__main__":
    run_test()