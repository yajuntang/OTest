import os

from flask import Flask, redirect, request
from flask_cors import CORS

from library.client.Client import Client
from server.app.controller.exec_controller import exec_api
from server.app.controller.page_version_controller import pages_version_api
from server.app.controller.pages_controller import pages_api
from server.app.controller.plan_controller import plan_api

app = Flask(__name__)
# 设置 session 时必须设置 secret_key；可通过环境变量 OTEST_SECRET_KEY 覆盖
app.secret_key = os.environ.get("OTEST_SECRET_KEY", "1ms9fm49g8wn3ir1")
CORS(app, supports_credentials=True, resources=r'/*')

app.register_blueprint(pages_api)  # 页面列表接口
app.register_blueprint(pages_version_api)  # 版本接口
app.register_blueprint(plan_api)  # 测试计划接口
app.register_blueprint(exec_api)  # 执行测试接口
session_id = None