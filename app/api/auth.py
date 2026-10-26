import hashlib

import requests
from flask import Blueprint, current_app, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..extensions import db
from ..models import User
from ..utils import fail, ok

auth_bp = Blueprint("auth_api", __name__)

ALLOWED_GENDERS = {"male", "female", "other"}
ALLOWED_GOALS = {"muscle_gain", "fat_loss", "shaping"}


def _mock_openid(code):
    """本地开发用稳定 mock openid，避免每次登录生成新用户。"""
    digest = hashlib.sha256(f"campus-gym:{code}".encode("utf-8")).hexdigest()
    return f"mock_{digest[:24]}"


def _resolve_openid(code):
    """开发环境使用 mock；生产环境调用微信 jscode2session。"""
    if current_app.config["WECHAT_MOCK_LOGIN"]:
        return _mock_openid(code)

    appid = current_app.config["WECHAT_APPID"]
    secret = current_app.config["WECHAT_SECRET"]
    if not appid or not secret:
        raise RuntimeError("WECHAT_APPID 或 WECHAT_SECRET 未配置")

    response = requests.get(
        "https://api.weixin.qq.com/sns/jscode2session",
        params={
            "appid": appid,
            "secret": secret,
            "js_code": code,
            "grant_type": "authorization_code",
        },
        timeout=8,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errcode"):
        raise RuntimeError(payload.get("errmsg", "微信登录失败"))
    return payload["openid"]


@auth_bp.post("/wechat-login")
def wechat_login():
    """微信小程序登录。

    小程序先调用 wx.login 获取 code，再请求本接口换取 JWT。
    本地 WECHAT_MOCK_LOGIN=true 时无需真实 AppID 即可测试。
    """
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code", "")).strip()
    if not code:
        return fail("缺少微信登录 code")

    try:
        openid = _resolve_openid(code)
    except Exception as exc:
        current_app.logger.exception("WeChat login failed")
        return fail(f"微信登录失败：{exc}", 502)

    user = User.query.filter_by(openid=openid).first()
    if user is None:
        user = User(openid=openid)
        db.session.add(user)
        db.session.commit()

    token = create_access_token(identity=str(user.id))
    return ok(
        {
            "access_token": token,
            "token_type": "Bearer",
            "user": user.to_dict(),
            "need_profile": not user.profile_completed,
        },
        "登录成功",
    )


@auth_bp.get("/profile")
@jwt_required()
def get_profile():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return fail("用户不存在", 404)
    return ok(user.to_dict())


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    """保存注册基础信息：昵称、年龄、身高、体重、性别、健身目标。"""
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return fail("用户不存在", 404)

    payload = request.get_json(silent=True) or {}
    try:
        age = int(payload.get("age"))
        height = float(payload.get("height"))
        weight = float(payload.get("weight"))
    except (TypeError, ValueError):
        return fail("年龄、身高和体重必须填写有效数字")

    gender = payload.get("gender")
    fitness_goal = payload.get("fitness_goal")
    if not 10 <= age <= 100:
        return fail("年龄需在 10-100 岁之间")
    if not 100 <= height <= 250:
        return fail("身高需在 100-250 cm 之间")
    if not 30 <= weight <= 300:
        return fail("体重需在 30-300 kg 之间")
    if gender not in ALLOWED_GENDERS:
        return fail("性别参数不正确")
    if fitness_goal not in ALLOWED_GOALS:
        return fail("健身目标参数不正确")

    user.nickname = str(payload.get("nickname") or user.nickname).strip()[:50]
    user.avatar_url = str(payload.get("avatar_url") or user.avatar_url).strip()
    user.age = age
    user.height = height
    user.weight = weight
    user.gender = gender
    user.fitness_goal = fitness_goal
    user.profile_completed = True

    db.session.commit()
    return ok(user.to_dict(), "基础资料保存成功")
