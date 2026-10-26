from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..extensions import db
from ..models import Equipment, EquipmentCategory
from ..services import release_expired_equipment, try_occupy_equipment
from ..utils import fail, ok

equipment_bp = Blueprint("equipment_api", __name__)


@equipment_bp.get("/categories")
def categories():
    release_expired_equipment()
    items = EquipmentCategory.query.order_by(
        EquipmentCategory.sort_order.asc(), EquipmentCategory.id.asc()
    ).all()
    return ok([item.to_dict(include_count=True) for item in items])


@equipment_bp.get("")
def equipment_list():
    # 查询列表前先清理超时占用，保证展示状态实时准确。
    release_expired_equipment()
    category_id = request.args.get("category_id", type=int)
    keyword = str(request.args.get("keyword", "")).strip()

    query = Equipment.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if keyword:
        query = query.filter(
            or_(
                Equipment.name.like(f"%{keyword}%"),
                Equipment.description.like(f"%{keyword}%"),
            )
        )

    items = query.order_by(Equipment.sort_order.asc(), Equipment.id.asc()).all()
    return ok([item.to_dict() for item in items])


@equipment_bp.get("/<int:equipment_id>")
def equipment_detail(equipment_id):
    release_expired_equipment()
    equipment = db.session.get(Equipment, equipment_id)
    if not equipment or not equipment.is_active:
        return fail("器械不存在", 404)
    return ok(equipment.to_dict(include_details=True))


@equipment_bp.post("/<int:equipment_id>/occupy")
@jwt_required()
def occupy_equipment(equipment_id):
    """训练流程尝试占用器械；已被其他用户占用时返回 409。"""
    user_id = int(get_jwt_identity())
    success, reason, equipment = try_occupy_equipment(equipment_id, user_id)

    if reason == "not_found":
        return fail("器械不存在", 404)
    if not success:
        return fail("该器械正在被其他同学训练，可以等待或更换训练部位", 409)
    return ok(equipment.to_dict(include_details=True), "器械占用成功")


@equipment_bp.post("/release-timeouts")
@jwt_required()
def release_timeouts():
    """供后台任务或管理员触发：释放超过 30 分钟的器械占用。"""
    released_count = release_expired_equipment()
    return ok({"released_count": released_count}, "超时器械检查完成")
