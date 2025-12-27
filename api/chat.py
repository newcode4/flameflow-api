"""
AI 챗봇 API 라우터
"""
from flask import Blueprint, request, jsonify
from services.chat_service import ChatService
from utils.logger import api_logger
import traceback

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
chat_service = ChatService()

@chat_bp.route("/<int:user_id>", methods=["POST"])
def chat(user_id):
    """
    AI 챗봇과 대화

    Request:
    {
        "question": "어제 방문자 수는 몇 명인가요?",
        "include_history": true  // 선택적, 기본값 true
    }

    Response:
    {
        "success": true,
        "answer": "어제 방문자 수는 1,234명입니다...",
        "tokens_used": 523,
        "remaining_balance": 9477
    }
    """
    try:
        data = request.json
        question = data.get("question")
        include_history = data.get("include_history", True)

        # 필수 필드 검증
        if not question:
            return jsonify({"success": False, "message": "질문이 필요합니다"}), 400

        # AI 챗봇 호출
        result = chat_service.chat(user_id, question, include_history)
        status_code = 200 if result.get("success") else 400

        return jsonify(result), status_code

    except Exception as e:
        api_logger.error(f"Chat error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@chat_bp.route("/history/<int:user_id>", methods=["GET"])
def get_history(user_id):
    """
    대화 히스토리 조회

    Query Params:
    - limit: 조회할 대화 수 (기본 20, 최대 100)

    Response:
    {
        "success": true,
        "data": [
            {
                "id": 1,
                "question": "...",
                "answer": "...",
                "tokens_used": 500,
                "created_at": "2025-01-01T00:00:00"
            },
            ...
        ]
    }
    """
    try:
        limit = request.args.get("limit", 20, type=int)
        limit = min(limit, 100)  # 최대 100개

        history = chat_service.get_chat_history(user_id, limit)

        return jsonify({"success": True, "data": history})

    except Exception as e:
        api_logger.error(f"Get history error: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500
