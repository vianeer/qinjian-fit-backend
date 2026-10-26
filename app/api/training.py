from datetime import date, datetime

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import TrainingPlan, TrainingPlanItem, TrainingSetRecord, User
from ..services import (
    build_training_plan,
    release_expired_equipment,
    release_plan_equipment,
)
from ..utils import fail, ok

training_bp = Blueprint("training_api", __name__)


def _current_user():
    return db.session.get(User, int(get_jwt_identity()))


def _owned_plan(plan_id, user):
    return TrainingPlan.query.filter_by(id=plan_id, user_id=user.id).first()


@training_bp.get("/plans/today")
@jwt_required()
def today_plan():
    release_expired_equipment()
    user = _current_user()
    plan = (
        TrainingPlan.query.filter_by(user_id=user.id, plan_date=date.today())
        .filter(TrainingPlan.status != "cancelled")
        .order_by(TrainingPlan.created_at.desc())
        .first()
    )
    return ok(plan.to_dict() if plan else None)


@training_bp.post("/plans/generate")
@jwt_required()
def generate_plan():
    """根据所选部位生成今日训练清单。"""
    user = _current_user()
    if not user or not user.profile_completed:
        return fail("请先完善年龄、身高、体重、性别和健身目标", 403)

    payload = request.get_json(silent=True) or {}
    raw_parts = payload.get("body_parts") or []
    if not isinstance(raw_parts, list):
        return fail("body_parts 必须是数组")

    body_parts = []
    for item in raw_parts:
        name = str(item).strip()
        if name and name not in body_parts:
            body_parts.append(name)

    if not 1 <= len(body_parts) <= 3:
        return fail("请选择 1-3 个训练部位")

    plan = build_training_plan(user, body_parts)
    if plan.total_sets == 0:
        return fail("所选部位暂时没有可用器械，请联系管理员", 404)
    return ok(plan.to_dict(), "训练计划生成成功")


@training_bp.get("/plans/<int:plan_id>")
@jwt_required()
def plan_detail(plan_id):
    release_expired_equipment()
    user = _current_user()
    plan = _owned_plan(plan_id, user)
    if not plan:
        return fail("训练计划不存在", 404)
    return ok(plan.to_dict())


@training_bp.post("/plans/<int:plan_id>/items/<int:item_id>/sets/<int:set_number>/complete")
@jwt_required()
def complete_set(plan_id, item_id, set_number):
    """完成一组后写入记录，并返回该动作配置的组间休息秒数。"""
    user = _current_user()
    plan = _owned_plan(plan_id, user)
    if not plan:
        return fail("训练计划不存在", 404)
    if plan.status == "completed":
        return fail("该训练计划已经结束")

    item = TrainingPlanItem.query.filter_by(id=item_id, plan_id=plan.id).first()
    if not item:
        return fail("训练动作不存在", 404)
    if set_number < 1 or set_number > item.target_sets:
        return fail("组号超出训练计划范围")

    record = TrainingSetRecord.query.filter_by(
        plan_item_id=item.id, set_number=set_number
    ).first()
    if not record:
        record = TrainingSetRecord(
            plan_id=plan.id,
            plan_item_id=item.id,
            set_number=set_number,
            completed_at=datetime.utcnow(),
        )
        db.session.add(record)
        db.session.flush()

    plan.completed_sets = TrainingSetRecord.query.filter_by(plan_id=plan.id).count()
    plan.status = "in_progress"
    db.session.commit()

    all_done = plan.completed_sets >= plan.total_sets
    return ok(
        {
            "set_record": record.to_dict(),
            "completed_sets": plan.completed_sets,
            "total_sets": plan.total_sets,
            "all_done": all_done,
            "rest_seconds": 0 if all_done else item.rest_seconds,
        },
        "本组已完成",
    )


@training_bp.post("/plans/<int:plan_id>/release-equipment")
@jwt_required()
def release_equipment_for_plan(plan_id):
    """放弃训练或异常兜底：批量释放该计划仍被当前用户占用的器械。"""
    user = _current_user()
    plan = _owned_plan(plan_id, user)
    if not plan:
        return fail("训练计划不存在", 404)

    released_ids = release_plan_equipment(plan, user.id)
    if plan.status not in {"completed", "cancelled"}:
        plan.status = "cancelled"
        db.session.commit()
    return ok({"released_equipment_ids": released_ids}, "本次训练器械已释放")


@training_bp.post("/plans/<int:plan_id>/finish")
@jwt_required()
def finish_plan(plan_id):
    """全部组次完成后结束训练并返回总结数据。"""
    user = _current_user()
    plan = _owned_plan(plan_id, user)
    if not plan:
        return fail("训练计划不存在", 404)

    actual_count = TrainingSetRecord.query.filter_by(plan_id=plan.id).count()
    if actual_count < plan.total_sets:
        return fail("还有未完成的训练组次", 400)

    if plan.status != "completed":
        plan.status = "completed"
        plan.completed_sets = actual_count
        plan.completed_at = datetime.utcnow()
        db.session.commit()

    # 正常结束训练：批量释放本次计划用到的全部器械。
    released_equipment_ids = release_plan_equipment(plan, user.id)

    duration_minutes = max(
        1, round((plan.completed_at - plan.created_at).total_seconds() / 60)
    )
    equipment_count = len({item.equipment_id for item in plan.items})
    return ok(
        {
            "plan_id": plan.id,
            "body_parts": plan.body_parts,
            "total_sets": plan.total_sets,
            "completed_sets": plan.completed_sets,
            "equipment_count": equipment_count,
            "duration_minutes": duration_minutes,
            "completed_at": plan.completed_at.isoformat(),
            "released_equipment_ids": released_equipment_ids,
            "message": "今日训练全部完成，记得补水并补充蛋白质。",
        },
        "训练完成",
    )


