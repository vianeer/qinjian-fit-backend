from flask import jsonify


def ok(data=None, message="success", status=200):
    """API 统一成功响应。"""
    return jsonify({"code": status, "message": message, "data": data}), status


def fail(message="请求参数错误", status=400, details=None):
    """API 统一失败响应。"""
    payload = {"code": status, "message": message, "data": None}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status
