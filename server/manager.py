import os
import eventlet
from flask import Flask
from flask_socketio import SocketIO
from server.server_config import HOST, PORT
from server.app.controller import exec_controller, pages_controller, plan_controller

# 建议在 requirements.txt 中补充 flask-socketio 和 eventlet
app = Flask(__name__, static_folder='static', static_url_path='/')

# 配置跨域，允许前端 React 页面进行 WebSocket 实时监听底层动作
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

app.register_blueprint(exec_controller.bp)
app.register_blueprint(pages_controller.bp)
app.register_blueprint(plan_controller.bp)


@app.route('/')
def index():
    return app.send_static_file('index.html')


# --- 新增：实时执行流的 WebSocket 命名空间 ---
@socketio.on('connect', namespace='/test_exec')
def handle_connect():
    print("前端 React 已连接到实时执行监控通道")


@socketio.on('disconnect', namespace='/test_exec')
def handle_disconnect():
    print("前端已断开实时监控")


if __name__ == '__main__':
    print(f"OTest 自动化测试中台启动中: http://{HOST}:{PORT}")

    # 替换原本的 app.run()，使用 socketio 启动，支撑双向长连接
    socketio.run(app, host=HOST, port=PORT, debug=True)