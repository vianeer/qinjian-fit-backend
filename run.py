"""本地开发入口。

运行：
    flask --app run.py run --host 0.0.0.0 --port 5000
或：
    python run.py
"""

from app import create_app
from app.services import start_occupancy_sweeper

app = create_app()

if __name__ == "__main__":
    # 后台线程每分钟释放一次超过 30 分钟的器械占用。
    start_occupancy_sweeper(app)
    # 关闭开发重载器，避免后台清理线程被重复启动。
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
