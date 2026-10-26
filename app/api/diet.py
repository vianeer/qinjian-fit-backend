from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import DietTemplate, TrainingPlan, User
from ..utils import fail, ok

diet_bp = Blueprint("diet_api", __name__)


def _select_template(goal, gender, body_part):
    """按目标、性别和训练部位打分，选择最匹配的管理员配置方案。"""
    candidates = DietTemplate.query.filter_by(
        fitness_goal=goal, is_enabled=True
    ).all()
    if not candidates:
        return None

    def score(template):
        value = 0
        if template.body_part == body_part:
            value += 8
        elif template.body_part is None:
            value += 2
        else:
            value -= 10
        if template.gender == gender:
            value += 4
        elif template.gender is None:
            value += 1
        return value

    ranked = sorted(candidates, key=score, reverse=True)
    return ranked[0] if ranked and score(ranked[0]) > -5 else None


@diet_bp.post("/plans/generate")
@jwt_required()
def generate_diet_plan():
    """根据用户目标、性别、体重及当日训练部位生成一日三餐建议。"""
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or not user.profile_completed:
        return fail("请先完善个人基础资料", 403)

    payload = request.get_json(silent=True) or {}
    body_parts = payload.get("body_parts") or []
    primary_body_part = str(payload.get("body_part", "")).strip()

    if not primary_body_part:
        today_plan = (
            TrainingPlan.query.filter_by(user_id=user.id, plan_date=date.today())
            .filter(TrainingPlan.status != "cancelled")
            .order_by(TrainingPlan.created_at.desc())
            .first()
        )
        if today_plan and today_plan.body_parts:
            body_parts = today_plan.body_parts
        if body_parts:
            primary_body_part = body_parts[0]

    template = _select_template(
        user.fitness_goal, user.gender, primary_body_part or None
    )
    if not template:
        return fail("暂未匹配到饮食方案，请在管理后台添加对应模板", 404)

    # 依据体重做小幅热量调整，避免仅按模板给出完全固定的热量。
    weight = float(user.weight)
    weight_adjust = round((weight - 65) * 8)
    gender_adjust = 120 if user.gender == "male" else -80 if user.gender == "female" else 0
    target_calories = max(
        1300, min(3500, template.total_calories + weight_adjust + gender_adjust)
    )
    ratio = target_calories / template.total_calories

    meals = []
    for meal in template.meals:
        data = meal.to_dict()
        data["target_calories"] = round(data["target_calories"] * ratio)
        meals.append(data)

    return ok(
        {
            "template_id": template.id,
            "template_name": template.name,
            "fitness_goal": user.fitness_goal,
            "gender": user.gender,
            "weight": weight,
            "body_part": primary_body_part or "通用",
            "target_calories": target_calories,
            "calorie_note": "热量为估算值，可按饥饿感和体重变化每周微调。",
            "tips": template.tips,
            "meals": meals,
        },
        "饮食方案生成成功",
    )
