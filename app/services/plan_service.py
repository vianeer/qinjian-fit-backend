from datetime import date

from ..extensions import db
from ..models import Equipment, TrainingPlan, TrainingPlanItem

GOAL_PRESETS = {
    "muscle_gain": {"sets": 4, "reps": "8-10", "rest": 90},
    "fat_loss": {"sets": 3, "reps": "12-15", "rest": 45},
    "shaping": {"sets": 3, "reps": "10-12", "rest": 60},
}


def build_training_plan(user, body_parts, plan_date=None):
    """根据训练部位和用户目标生成并持久化训练计划。

    每个部位优先选择 2 个启用中的器械；有氧分类只安排 1 项。
    器械自身的推荐组数/次数会覆盖目标预设，保证管理员修改后立即生效。
    """
    target_date = plan_date or date.today()
    preset = GOAL_PRESETS.get(user.fitness_goal or "shaping")

    # 同一天重复生成计划时，将旧的未完成计划取消，保留历史记录。
    old_plans = TrainingPlan.query.filter(
        TrainingPlan.user_id == user.id,
        TrainingPlan.plan_date == target_date,
        TrainingPlan.status.in_(["draft", "in_progress"]),
    ).all()
    for old_plan in old_plans:
        old_plan.status = "cancelled"

    plan = TrainingPlan(
        user_id=user.id,
        plan_date=target_date,
        body_parts=body_parts,
        status="draft",
    )
    db.session.add(plan)
    db.session.flush()

    order = 0
    total_sets = 0
    for body_part in body_parts:
        limit = 1 if body_part == "有氧" else 2
        equipment_items = (
            Equipment.query.join(Equipment.category)
            .filter(
                Equipment.is_active.is_(True),
                Equipment.category.has(name=body_part),
            )
            .order_by(Equipment.sort_order.asc(), Equipment.id.asc())
            .limit(limit)
            .all()
        )
        if not equipment_items:
            continue

        for equipment in equipment_items:
            order += 1
            target_sets = equipment.recommended_sets or preset["sets"]
            item = TrainingPlanItem(
                plan_id=plan.id,
                equipment_id=equipment.id,
                sort_order=order,
                target_sets=target_sets,
                target_reps=equipment.recommended_reps or preset["reps"],
                rest_seconds=equipment.rest_seconds
                if equipment.rest_seconds is not None
                else preset["rest"],
            )
            total_sets += target_sets
            db.session.add(item)

    plan.total_sets = total_sets
    db.session.commit()
    return plan
