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

app.register_blueprint(pages_api)
app.register_blueprint(pages_version_api)
app.register_blueprint(plan_api)
app.register_blueprint(exec_api)
session_id = None


@app.route('/static/task_report')
def static_task_report():
    return redirect(request.path)

@app.route('/')
def index():
    return redirect('/static/index.html')


@app.route('/test_pages')
def test_pages():
    return redirect('/static/index.html')


@app.route('/test_plans')
def test_plans():
    return redirect('/static/index.html')


@app.route('/test_exec')
def test_exec():
    return redirect('/static/index.html')



if __name__ == '__main__':
    Client.run('localhost', 9000)
    app.run('localhost', 9000)


