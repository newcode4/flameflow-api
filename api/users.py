"""
사용자 관리 API 라우터
"""
from flask import Blueprint, request, jsonify
from services.user_service import UserService
from utils.logger import api_logger
import traceback

users_bp = Blueprint('users', __name__, url_prefix='/api/user')
user_service = UserService()

@users_bp.route("/register", methods=["POST"])
def register():
    """
    WordPress 사용자 등록

    Request:
    {
        "wp_user_id": 123,
        "email": "user@example.com",
        "ga4_property_id": "488770841",
        "token_balance": 10000  // 선택적
    }

    Response:
    {
        "success": true,
        "user_id": 1,
        "message": "사용자 등록 완료",
        "token_balance": 10000
    }
    """
    try:
        data = request.json
        wp_user_id = data.get("wp_user_id")
        email = data.get("email")
        property_id = data.get("ga4_property_id")
        token_balance = data.get("token_balance")

        # 필수 필드 검증
        if not wp_user_id or not email or not property_id:
            return jsonify({
                "success": False,
                "message": "필수 정보 누락 (wp_user_id, email, ga4_property_id)"
            }), 400

        # 사용자 등록
        result = user_service.register_user(wp_user_id, email, property_id, token_balance)

        status_code = 200 if result.get("success") else 400
        return jsonify(result), status_code

    except Exception as e:
        api_logger.error(f"Register error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@users_bp.route("/profile/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    """
    사용자 프로필 조회

    Response:
    {
        "user_id": 1,
        "wp_user_id": 123,
        "email": "user@example.com",
        "token_balance": 9500,
        "plan": "beta",
        "user_context": {...},
        "ga4_property_id": "488770841",
        "created_at": "2025-01-01T00:00:00"
    }
    """
    try:
        profile = user_service.get_user_profile(user_id)

        if profile:
            return jsonify({"success": True, "data": profile})
        else:
            return jsonify({"success": False, "message": "사용자를 찾을 수 없습니다"}), 404

    except Exception as e:
        api_logger.error(f"Get profile error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@users_bp.route("/context/<int:user_id>", methods=["PUT"])
def update_context(user_id):
    """
    사용자 AI 학습 컨텍스트 업데이트

    Request:
    {
        "business_type": "쇼핑몰",
        "kpi": ["매출", "전환율", "ROAS"],
        "goals": "월 매출 1000만원 달성",
        "target_audience": "20-30대 여성",
        "additional_info": "프리미엄 화장품 판매"
    }
    """
    try:
        context_data = request.json

        result = user_service.update_user_ai_context(user_id, context_data)
        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        api_logger.error(f"Update context error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@users_bp.route("/tokens/<int:user_id>", methods=["GET"])
def check_balance(user_id):
    """토큰 잔액 조회"""
    try:
        balance = user_service.check_token_balance(user_id)

        if balance is not None:
            return jsonify({"success": True, "token_balance": balance})
        else:
            return jsonify({"success": False, "message": "사용자를 찾을 수 없습니다"}), 404

    except Exception as e:
        api_logger.error(f"Check balance error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@users_bp.route("/tokens/<int:user_id>/charge", methods=["POST"])
def charge_tokens(user_id):
    """
    토큰 충전

    Request:
    {
        "amount": 5000,
        "payment_method": "credit_card"  // 선택적
    }
    """
    try:
        data = request.json
        amount = data.get("amount")
        payment_method = data.get("payment_method", "manual")

        if not amount or amount <= 0:
            return jsonify({"success": False, "message": "유효하지 않은 충전 금액"}), 400

        result = user_service.charge_tokens(user_id, amount, payment_method)
        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        api_logger.error(f"Charge tokens error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500
