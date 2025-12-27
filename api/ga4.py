"""
GA4 데이터 동기화 API 라우터
"""
from flask import Blueprint, request, jsonify
from services.ga4_service import GA4Service
from utils.logger import api_logger
import traceback

ga4_bp = Blueprint('ga4', __name__, url_prefix='/api/ga4')
ga4_service = GA4Service()

@ga4_bp.route("/sync/<int:user_id>", methods=["POST"])
def sync_user_data(user_id):
    """
    사용자의 GA4 데이터 전체 동기화

    Request:
    {
        "days": 30  // 선택적, 기본값 30일
    }

    Response:
    {
        "success": true,
        "data_id": 123,
        "property_id": "488770841",
        "date_range": "2024-12-01 ~ 2025-01-01",
        "summary": {...},
        "api_calls": 15
    }
    """
    try:
        data = request.json or {}
        days = data.get("days")

        result = ga4_service.sync_user_data(user_id, days)
        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        api_logger.error(f"Sync user data error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@ga4_bp.route("/sync/<int:user_id>/incremental", methods=["POST"])
def sync_incremental(user_id):
    """
    증분 데이터 동기화 (이전 날짜 이후 데이터만)

    Response:
    {
        "success": true,
        "days_added": 3,
        "data_id": 124,
        "message": "3일간의 데이터 추가됨"
    }
    """
    try:
        result = ga4_service.sync_incremental(user_id)
        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        api_logger.error(f"Incremental sync error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@ga4_bp.route("/summary/<int:user_id>", methods=["GET"])
def get_summary(user_id):
    """
    사용자의 GA4 데이터 요약 조회

    Response:
    {
        "date_range": {...},
        "summary": {...},
        "top_pages": [...],
        "traffic_sources": [...],
        "last_updated": "2025-01-01T00:00:00"
    }
    """
    try:
        summary = ga4_service.get_user_ga4_summary(user_id)

        if summary:
            return jsonify({"success": True, "data": summary})
        else:
            return jsonify({
                "success": False,
                "message": "GA4 데이터가 없습니다. 먼저 동기화를 진행하세요."
            }), 404

    except Exception as e:
        api_logger.error(f"Get summary error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@ga4_bp.route("/property/<int:user_id>", methods=["GET"])
def get_property_id(user_id):
    """사용자의 GA4 Property ID 조회"""
    try:
        property_id = ga4_service.get_property_id(user_id)

        if property_id:
            return jsonify({"success": True, "property_id": property_id})
        else:
            return jsonify({"success": False, "message": "GA4 계정이 없습니다"}), 404

    except Exception as e:
        api_logger.error(f"Get property ID error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@ga4_bp.route("/property/<int:user_id>", methods=["PUT"])
def update_property_id(user_id):
    """
    사용자의 GA4 Property ID 변경

    Request:
    {
        "property_id": "123456789"
    }
    """
    try:
        data = request.json
        new_property_id = data.get("property_id")

        if not new_property_id:
            return jsonify({"success": False, "message": "property_id가 필요합니다"}), 400

        result = ga4_service.update_property_id(user_id, new_property_id)
        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        api_logger.error(f"Update property ID error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500
