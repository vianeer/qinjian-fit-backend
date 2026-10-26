import threading
import time
from datetime import datetime, timedelta

from sqlalchemy import or_, update

from ..extensions import db
from ..models import Equipment

OCCUPANCY_TIMEOUT_MINUTES = 30


def release_expired_equipment(commit=True):
    """释放超过 30 分钟或占用时间缺失的异常占用记录。"""
    cutoff = datetime.utcnow() - timedelta(minutes=OCCUPANCY_TIMEOUT_MINUTES)
    result = db.session.execute(
        update(Equipment)
        .where(
            Equipment.occupy_status == 1,
            or_(
                Equipment.occupy_start_time.is_(None),
                Equipment.occupy_start_time <= cutoff,
            ),
        )
        .values(
            occupy_user_id=None,
            occupy_start_time=None,
            occupy_status=0,
        )
    )
    if commit:
        db.session.commit()
    return result.rowcount or 0


def try_occupy_equipment(equipment_id, user_id):
    """原子尝试占用器械，防止两个用户同时占用成功。

    返回 (success, reason, equipment)。
    """
    release_expired_equipment(commit=True)
    equipment = db.session.get(Equipment, equipment_id)
    if not equipment or not equipment.is_active:
        return False, "not_found", None

    # 同一用户重复进入详情时视为占用成功，不重置开始时间。
    if equipment.occupy_status == 1 and equipment.occupy_user_id == user_id:
        return True, "already_occupied", equipment

    result = db.session.execute(
        update(Equipment)
        .where(
            Equipment.id == equipment_id,
            Equipment.is_active.is_(True),
            or_(
                Equipment.occupy_status == 0,
                Equipment.occupy_status.is_(None),
            ),
        )
        .values(
            occupy_user_id=user_id,
            occupy_start_time=datetime.utcnow(),
            occupy_status=1,
        )
    )
    if result.rowcount != 1:
        db.session.rollback()
        return False, "occupied", None

    db.session.commit()
    return True, "occupied", db.session.get(Equipment, equipment_id)


def release_plan_equipment(plan, user_id):
    """批量释放训练计划使用的器械，只释放仍属于当前用户的占用。"""
    equipment_ids = list({item.equipment_id for item in plan.items})
    if not equipment_ids:
        return []

    equipment_items = Equipment.query.filter(
        Equipment.id.in_(equipment_ids),
        Equipment.occupy_status == 1,
        Equipment.occupy_user_id == user_id,
    ).all()
    released_ids = []
    for equipment in equipment_items:
        equipment.occupy_user_id = None
        equipment.occupy_start_time = None
        equipment.occupy_status = 0
        released_ids.append(equipment.id)

    db.session.commit()
    return released_ids


def start_occupancy_sweeper(app, interval_seconds=60):
    """启动后台守护线程，定时清理超时占用。"""
    if app.extensions.get("occupancy_sweeper_started"):
        return
    app.extensions["occupancy_sweeper_started"] = True

    def worker():
        while True:
            time.sleep(interval_seconds)
            try:
                with app.app_context():
                    release_expired_equipment(commit=True)
            except Exception:
                app.logger.exception("自动释放超时器械失败")

    thread = threading.Thread(target=worker, name="equipment-timeout-sweeper", daemon=True)
    thread.start()
