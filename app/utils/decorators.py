from functools import wraps

from flask import flash, redirect, session, url_for


def admin_required(view):
    """管理后台页面鉴权：未登录时跳转到后台登录页。"""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("请先登录管理后台", "warning")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped
