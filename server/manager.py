import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from server.app.controller.exec_controller import exec_api
from server.app.controller.page_version_controller import pages_version_api
from server.app.controller.pages_controller import pages_api
from server.app.controller.plan_controller import plan_api

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
app.secret_key = os.environ.get("OTEST_SECRET_KEY", "1ms9fm49g8wn3ir1")

cors_origins = os.environ.get("OTEST_CORS_ORIGINS", "http://localhost:9000,http://127.0.0.1:9000")
CORS(
    app,
    supports_credentials=True,
    resources=r"/*",
    origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
)

app.register_blueprint(pages_api)  # 页面列表接口
app.register_blueprint(pages_version_api)  # 版本接口
app.register_blueprint(plan_api)  # 测试计划接口
app.register_blueprint(exec_api)  # 执行测试接口
session_id = None


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:path>")
def static_fallback(path):
    target = os.path.join(STATIC_DIR, path)
    if os.path.isfile(target):
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, "index.html")


if __name__ == "__main__":
    host = os.environ.get("OTEST_HOST", "127.0.0.1")
    port = int(os.environ.get("OTEST_PORT", "9000"))
    debug = os.environ.get("OTEST_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)
