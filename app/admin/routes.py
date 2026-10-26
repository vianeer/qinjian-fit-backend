import json
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..extensions import db
from ..models import (
    Admin,
    DietMeal,
    DietTemplate,
    Equipment,
    EquipmentCategory,
    EquipmentOccupancyReport,
    KnowledgeArticle,
    KnowledgeCategory,
    User,
)
from ..utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/", methods=["GET"])
def index():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("admin.login"))


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session.clear()
            session["admin_id"] = admin.id
            session["admin_name"] = admin.display_name
            flash("登录成功", "success")
            return redirect(url_for("admin.dashboard"))
        flash("用户名或密码错误", "danger")
    return render_template("admin/login.html")


@admin_bp.post("/logout")
def logout():
    session.clear()
    flash("已退出登录", "info")
    return redirect(url_for("admin.login"))


@admin_bp.get("/dashboard")
@admin_required
def dashboard():
    stats = {
        "equipment_count": Equipment.query.count(),
        "user_count": User.query.count(),
        "article_count": KnowledgeArticle.query.count(),
        "diet_count": DietTemplate.query.count(),
        "report_count": EquipmentOccupancyReport.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.get("/equipment")
@admin_required
def equipment_list():
    items = (
        Equipment.query.join(EquipmentCategory)
        .order_by(EquipmentCategory.sort_order, Equipment.sort_order)
        .all()
    )
    return render_template("admin/equipment_list.html", items=items)


@admin_bp.route("/equipment/new", methods=["GET", "POST"])
@admin_required
def equipment_new():
    return _equipment_form()


@admin_bp.route("/equipment/<int:equipment_id>/edit", methods=["GET", "POST"])
@admin_required
def equipment_edit(equipment_id):
    equipment = db.get_or_404(Equipment, equipment_id)
    return _equipment_form(equipment)


def _equipment_form(equipment=None):
    categories = EquipmentCategory.query.order_by(EquipmentCategory.sort_order).all()
    if request.method == "POST":
        try:
            image_urls = [
                line.strip()
                for line in request.form.get("image_urls", "").splitlines()
                if line.strip()
            ]
            obj = equipment or Equipment()
            obj.category_id = int(request.form.get("category_id"))
            obj.name = request.form.get("name", "").strip()
            obj.cover_url = request.form.get("cover_url", "").strip()
            obj.image_urls = image_urls
            obj.description = request.form.get("description", "").strip()
            obj.action_key_points = request.form.get("action_key_points", "").strip()
            obj.force_points = request.form.get("force_points", "").strip()
            obj.common_mistakes = request.form.get("common_mistakes", "").strip()
            obj.video_url = request.form.get("video_url", "").strip()
            obj.recommended_sets = int(request.form.get("recommended_sets", 3))
            obj.recommended_reps = request.form.get("recommended_reps", "12").strip()
            obj.rest_seconds = int(request.form.get("rest_seconds", 60))
            obj.sort_order = int(request.form.get("sort_order", 0))
            obj.is_active = request.form.get("is_active") == "on"

            # 管理员异常兜底：手动校正设备空闲/占用状态。
            obj.occupy_status = int(request.form.get("occupy_status", 0))
            if obj.occupy_status == 1:
                raw_user_id = request.form.get("occupy_user_id", "").strip()
                raw_start_time = request.form.get("occupy_start_time", "").strip()
                obj.occupy_user_id = int(raw_user_id) if raw_user_id else None
                obj.occupy_start_time = (
                    datetime.fromisoformat(raw_start_time)
                    if raw_start_time
                    else datetime.utcnow()
                )
            else:
                obj.occupy_user_id = None
                obj.occupy_start_time = None

            if not obj.name or not obj.description:
                raise ValueError("器械名称和说明不能为空")
            if equipment is None:
                db.session.add(obj)
            db.session.commit()
            flash("器械资料已保存", "success")
            return redirect(url_for("admin.equipment_list"))
        except (TypeError, ValueError) as exc:
            db.session.rollback()
            flash(f"保存失败：{exc}", "danger")
    return render_template(
        "admin/equipment_form.html", equipment=equipment, categories=categories
    )


@admin_bp.post("/equipment/<int:equipment_id>/delete")
@admin_required
def equipment_delete(equipment_id):
    equipment = db.get_or_404(Equipment, equipment_id)
    db.session.delete(equipment)
    db.session.commit()
    flash("器械已删除", "success")
    return redirect(url_for("admin.equipment_list"))


@admin_bp.get("/knowledge")
@admin_required
def knowledge_list():
    items = (
        KnowledgeArticle.query.join(KnowledgeCategory)
        .order_by(KnowledgeCategory.sort_order, KnowledgeArticle.published_at.desc())
        .all()
    )
    return render_template("admin/knowledge_list.html", items=items)


@admin_bp.route("/knowledge/new", methods=["GET", "POST"])
@admin_required
def knowledge_new():
    return _knowledge_form()


@admin_bp.route("/knowledge/<int:article_id>/edit", methods=["GET", "POST"])
@admin_required
def knowledge_edit(article_id):
    article = db.get_or_404(KnowledgeArticle, article_id)
    return _knowledge_form(article)


def _knowledge_form(article=None):
    categories = KnowledgeCategory.query.order_by(KnowledgeCategory.sort_order).all()
    if request.method == "POST":
        try:
            obj = article or KnowledgeArticle()
            obj.category_id = int(request.form.get("category_id"))
            obj.title = request.form.get("title", "").strip()
            obj.summary = request.form.get("summary", "").strip()
            obj.content = request.form.get("content", "").strip()
            obj.cover_url = request.form.get("cover_url", "").strip()
            obj.source = request.form.get("source", "校园健身房").strip()
            obj.is_published = request.form.get("is_published") == "on"
            if not obj.title or not obj.content:
                raise ValueError("标题和正文不能为空")
            if article is None:
                db.session.add(obj)
            db.session.commit()
            flash("知识文章已保存", "success")
            return redirect(url_for("admin.knowledge_list"))
        except (TypeError, ValueError) as exc:
            db.session.rollback()
            flash(f"保存失败：{exc}", "danger")
    return render_template(
        "admin/knowledge_form.html", article=article, categories=categories
    )


@admin_bp.post("/knowledge/<int:article_id>/delete")
@admin_required
def knowledge_delete(article_id):
    article = db.get_or_404(KnowledgeArticle, article_id)
    db.session.delete(article)
    db.session.commit()
    flash("知识文章已删除", "success")
    return redirect(url_for("admin.knowledge_list"))


@admin_bp.get("/diets")
@admin_required
def diet_list():
    items = DietTemplate.query.order_by(DietTemplate.id.desc()).all()
    return render_template("admin/diet_list.html", items=items)


@admin_bp.route("/diets/new", methods=["GET", "POST"])
@admin_required
def diet_new():
    return _diet_form()


@admin_bp.route("/diets/<int:template_id>/edit", methods=["GET", "POST"])
@admin_required
def diet_edit(template_id):
    template = db.get_or_404(DietTemplate, template_id)
    return _diet_form(template)


def _meals_to_json(template):
    if not template:
        return '[{"meal_type":"breakfast","food_items":["燕麦 50g","鸡蛋 2 个"],"target_calories":500,"sort_order":10}]'
    meals = []
    for meal in template.meals:
        meals.append(
            {
                "meal_type": meal.meal_type,
                "food_items": meal.food_items,
                "target_calories": meal.target_calories,
                "sort_order": meal.sort_order,
            }
        )
    return json.dumps(meals, ensure_ascii=False, indent=2)


def _diet_form(template=None):
    if request.method == "POST":
        try:
            form_data = {
                "name": request.form.get("name", "").strip(),
                "fitness_goal": request.form.get("fitness_goal", "shaping"),
                "gender": request.form.get("gender") or None,
                "body_part": request.form.get("body_part") or None,
                "meal_count": int(request.form.get("meal_count", 3)),
                "total_calories": int(request.form.get("total_calories", 2000)),
                "tips": request.form.get("tips", "").strip(),
                "is_enabled": request.form.get("is_enabled") == "on",
            }
            meals = json.loads(request.form.get("meals_json", "[]"))
            if not isinstance(meals, list) or not meals:
                raise ValueError("餐次 JSON 必须是非空数组")
            if not form_data["name"]:
                raise ValueError("方案名称不能为空")

            obj = template or DietTemplate()
            for key, value in form_data.items():
                setattr(obj, key, value)
            if template is None:
                db.session.add(obj)
            db.session.flush()
            DietMeal.query.filter_by(template_id=obj.id).delete()
            for index, meal in enumerate(meals):
                db.session.add(
                    DietMeal(
                        template_id=obj.id,
                        meal_type=meal.get("meal_type", "snack"),
                        food_items=meal.get("food_items") or [],
                        target_calories=int(meal.get("target_calories", 0)),
                        sort_order=int(meal.get("sort_order", (index + 1) * 10)),
                    )
                )
            db.session.commit()
            flash("饮食方案已保存", "success")
            return redirect(url_for("admin.diet_list"))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            db.session.rollback()
            flash(f"保存失败：{exc}", "danger")
    return render_template(
        "admin/diet_form.html", template=template, meals_json=_meals_to_json(template)
    )


@admin_bp.post("/diets/<int:template_id>/delete")
@admin_required
def diet_delete(template_id):
    template = db.get_or_404(DietTemplate, template_id)
    db.session.delete(template)
    db.session.commit()
    flash("饮食方案已删除", "success")
    return redirect(url_for("admin.diet_list"))


@admin_bp.get("/reports")
@admin_required
def report_list():
    items = (
        EquipmentOccupancyReport.query.join(Equipment)
        .order_by(EquipmentOccupancyReport.created_at.desc())
        .limit(200)
        .all()
    )
    return render_template("admin/report_list.html", items=items, now=datetime.utcnow())

