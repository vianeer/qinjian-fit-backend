from sqlalchemy import inspect, text

from .extensions import db


def ensure_sqlite_occupancy_columns():
    """为已有 SQLite 数据库增量补充器械占用字段。

    只执行 ALTER TABLE ADD COLUMN，不删除、不重建任何表和字段。
    新数据库会直接由 SQLAlchemy 模型创建完整字段。
    """
    if not str(db.engine.url).startswith("sqlite"):
        return []

    inspector = inspect(db.engine)
    if "equipment" not in inspector.get_table_names():
        return []

    existing = {column["name"] for column in inspector.get_columns("equipment")}
    definitions = {
        "occupy_user_id": "INTEGER",
        "occupy_start_time": "DATETIME",
        "occupy_status": "INTEGER NOT NULL DEFAULT 0",
    }

    added = []
    for column_name, definition in definitions.items():
        if column_name in existing:
            continue
        db.session.execute(
            text(f"ALTER TABLE equipment ADD COLUMN {column_name} {definition}")
        )
        added.append(column_name)

    if added:
        db.session.commit()
    return added
