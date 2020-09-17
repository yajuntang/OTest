from flask import Flask, redirect, request
from flask_cors import CORS

from library.client.Client import Client
from server.app.controller.exec_controller import exec_api
from server.app.controller.page_version_controller import pages_version_api
from server.app.controller.pages_controller import pages_api
from server.app.controller.plan_controller import plan_api

app = Flask(__name__)
app.secret_key = "1ms9fm49g8wn3ir1"  # 设置session时，必须要加盐，否则报错
CORS(app, supports_credentials=True, resources=r'/*')

app.register_blueprint(pages_api)  # 页面列表接口
app.register_blueprint(pages_version_api)  # 版本接口
app.register_blueprint(plan_api)  # 测试计划接口
app.register_blueprint(exec_api)  # 执行测试接口
session_id = None


@app.route('/static/task_report')
def static_task_report():
    """
    显示任务报告
    :return:
    """
    return redirect(request.path)


@app.route('/')
def index():
    """
    前端页面
    :return:
    """
    return redirect('/static/index.html')


@app.route('/test_pages')
def test_pages():
    """
    前端页面
    :return:
    """
    return redirect('/static/index.html')


@app.route('/test_plans')
def test_plans():
    """
    前端页面
    :return:
    """
    return redirect('/static/index.html')


@app.route('/test_exec')
def test_exec():
    """
    前端页面
    :return:
    """
    return redirect('/static/index.html')


if __name__ == '__main__':
    Client.run('localhost', 9000)
    app.run('localhost', 9000)
