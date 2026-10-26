import sqlite3

from flask import Flask, jsonify
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import Config
from .extensions import cors, db, jwt


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """SQLite 默认不启用外键约束，这里为每个连接开启外键检查。"""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app(config_class=Config):
    """创建并配置 Flask 应用。"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)

    # 已有 SQLite 数据库自动补齐器械占用字段，不重建表。
    if str(app.config["SQLALCHEMY_DATABASE_URI"]).startswith("sqlite"):
        from .db_migrations import ensure_sqlite_occupancy_columns

        with app.app_context():
            ensure_sqlite_occupancy_columns()
    # 小程序请求来自非浏览器环境，API 开放跨域；管理后台使用同源 Session。
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    register_jwt_handlers()
    register_blueprints(app)
    register_cli(app)
    register_error_handlers(app)

    return app


def register_jwt_handlers():
    """设置 JWT 解析后自动查询当前用户，并返回统一错误结构。"""
    from .models import User

    @jwt.user_lookup_loader
    def load_user(_jwt_header, jwt_data):
        user_id = jwt_data.get("sub")
        if not user_id:
            return None
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"code": 401, "message": "请先登录", "detail": reason}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"code": 401, "message": "登录状态无效", "detail": reason}), 401

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return jsonify({"code": 401, "message": "登录已过期，请重新登录"}), 401


def register_blueprints(app):
    from .admin import admin_bp
    from .api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")


def register_cli(app):
    """注册数据库初始化和演示数据命令。"""

    @app.cli.command("init-db")
    def init_db_command():
        """只创建表，不写入业务数据。"""
        db.create_all()
        print("数据库表创建完成。")

    @app.cli.command("seed-db")
    def seed_db_command():
        """创建表并写入校园健身房演示数据，可重复执行。"""
        from .seed import seed_database

        db.create_all()
        seed_database()
        print("演示数据初始化完成。")

    @app.cli.command("release-equipment-timeouts")
    def release_equipment_timeouts_command():
        """手动执行一次超时器械释放，适合生产环境定时任务调用。"""
        from .services import release_expired_equipment

        count = release_expired_equipment()
        print(f"已释放超时占用器械 {count} 台。")


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"code": 404, "message": "接口或页面不存在"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.exception("Server error: %s", error)
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500




