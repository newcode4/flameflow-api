from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import traceback

# 로컬 모듈 import
# 주의: 해당 파일들이 같은 디렉토리에 있어야 합니다.
from supabase_client import (
    supabase,
    get_user_by_wp_id,
    get_latest_ga4_data,
    save_chat_history,
    update_token_balance,
    save_ga4_data
)
from ga4_extractor_template import GA4TemplateExtractor
from ga4_config import PROPERTY_ID, CREDENTIALS_PATH

# .env 파일 로드
load_dotenv()

app = Flask(__name__)
CORS(app)  # WordPress 또는 프론트엔드 앱에서 호출 가능하도록 허용

# Claude API 클라이언트 초기화 (환경변수에서 API 키 로드)
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.route("/")
def home():
    """서버 상태 확인을 위한 기본 엔드포인트"""
    return jsonify({
        "service": "FrameFlow GA4 AI API",
        "version": "1.0",
        "status": "running",
        "message": "서버가 정상적으로 작동 중입니다."
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    AI 챗봇 엔드포인트: GA4 데이터를 기반으로 질문에 답변
    
    Request Body:
    {
        "user_id": 1,           # Supabase 사용자 고유 ID
        "question": "어제 방문자 몇 명?"
    }
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        question = data.get("question")
        
        # 필수 파라미터 체크
        if not user_id or not question:
            return jsonify({"error": "user_id와 question이 필요합니다."}), 400
        
        # 1. Supabase에서 해당 사용자의 최신 GA4 데이터 조회
        ga4_data = get_latest_ga4_data(user_id)
        
        if not ga4_data:
            return jsonify({"error": "조회된 GA4 데이터가 없습니다. 먼저 데이터 동기화를 진행하세요."}), 404
        
        # 2. Claude에게 제공할 컨텍스트 생성
        raw_data = ga4_data["raw_data"]
        
        context = f"""
당신은 GA4 데이터 분석 전문가입니다.
다음은 사용자의 GA4 데이터 요약입니다:

[분석 기간]
{raw_data['info']['date_range']['start']} ~ {raw_data['info']['date_range']['end']}

[핵심 지표 요약]
- 활성 사용자: {raw_data.get('summary', {}).get('activeUsers', 0):,}명
- 세션: {raw_data.get('summary', {}).get('sessions', 0):,}개
- 페이지뷰: {raw_data.get('summary', {}).get('screenPageViews', 0):,}회
- 총 수익: ₩{raw_data.get('summary', {}).get('purchaseRevenue', 0):,.0f}
- 거래 수: {raw_data.get('summary', {}).get('transactions', 0):,.0f}건
- 이탈률: {raw_data.get('summary', {}).get('bounceRate', 0):.2%}

[인기 페이지 상위 5개]
{format_top_pages(raw_data.get('pages', [])[:5])}

[주요 유입경로 상위 5개]
{format_traffic_sources(raw_data.get('traffic_sources', [])[:5])}

사용자 질문에 대해 위 데이터를 기반으로 짧고 명확하게 답변하세요. 
모든 숫자는 가독성을 위해 천 단위 쉼표(,)를 사용하세요.
"""
        
        # 3. Claude AI 모델 호출
        response = claude.messages.create(
            model="claude-3-haiku-20240307", # 모델명 확인 필요
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": context + f"\n\n사용자 질문: {question}"
                }
            ]
        )
        
        answer = response.content[0].text
        # 사용된 토큰 계산
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        
        # 4. Supabase에 대화 내역 저장
        save_chat_history(user_id, question, answer, tokens_used)
        
        # 5. 사용자 토큰 잔액 차감
        remaining_balance = update_token_balance(user_id, tokens_used)
        
        return jsonify({
            "answer": answer,
            "tokens_used": tokens_used,
            "remaining_balance": remaining_balance
        })
        
    except Exception as e:
        print(f"Chat Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/ga4/sync", methods=["POST"])
def sync_ga4():
    """
    GA4 실시간 데이터 동기화 엔드포인트
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        days = data.get("days", 30)

        if not user_id:
            return jsonify({"error": "user_id가 누락되었습니다."}), 400

        # GA4 데이터 추출 실행
        extractor = GA4TemplateExtractor(PROPERTY_ID, CREDENTIALS_PATH)
        all_data = extractor.extract_data(days)

        # 동기화 날짜 설정
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # 추출된 데이터를 Supabase에 업로드
        result = save_ga4_data(user_id, str(start_date), str(end_date), all_data)

        return jsonify({
            "status": "success",
            "data_id": result.get("id"),
            "api_calls": all_data["info"]["api_calls"],
            "summary": all_data.get("summary", {})
        })

    except Exception as e:
        print(f"Sync Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

# ============================================
# MVP 추가 엔드포인트 (2025-12-27)
# ============================================

@app.route("/api/user/register", methods=["POST"])
def register_user():
    """WordPress에서 사용자 등록"""
    try:
        data = request.json
        wp_user_id = data.get("wp_user_id")
        email = data.get("email")
        property_id = data.get("property_id")

        if not all([wp_user_id, email, property_id]):
            return jsonify({"error": "필수 정보 누락"}), 400

        # 1. users 테이블에 등록
        user_response = supabase.table("users").insert({
            "wp_user_id": wp_user_id,
            "email": email,
            "token_balance": 100000  # 초기 토큰 10만개
        }).execute()

        user_id = user_response.data[0]["id"]

        # 2. ga4_accounts 테이블에 Property ID 저장
        supabase.table("ga4_accounts").insert({
            "user_id": user_id,
            "property_id": property_id,
            "credentials": None  # 공통 service-account 사용
        }).execute()

        return jsonify({
            "success": True,
            "user_id": user_id,
            "message": "사용자 등록 완료"
        })

    except Exception as e:
        print(f"Register Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/user/get-by-wp-id", methods=["POST"])
def get_user_by_wp_id():
    """WordPress ID로 Supabase user_id 찾기"""
    try:
        data = request.json
        wp_user_id = data.get("wp_user_id")

        if not wp_user_id:
            return jsonify({"error": "wp_user_id 필요"}), 400

        response = supabase.table("users").select("*").eq("wp_user_id", wp_user_id).execute()

        if not response.data:
            return jsonify({"error": "사용자 없음"}), 404

        return jsonify({
            "success": True,
            "user": response.data[0]
        })

    except Exception as e:
        print(f"Get User Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/ga4/sync-user", methods=["POST"])
def sync_user_ga4():
    """사용자별 GA4 데이터 수집"""
    try:
        data = request.json
        wp_user_id = data.get("wp_user_id")

        if not wp_user_id:
            return jsonify({"error": "wp_user_id 필요"}), 400

        # 1. user_id 찾기
        user_response = supabase.table("users").select("id").eq("wp_user_id", wp_user_id).execute()
        if not user_response.data:
            return jsonify({"error": "사용자 없음"}), 404

        user_id = user_response.data[0]["id"]

        # 2. Property ID 찾기
        ga4_response = supabase.table("ga4_accounts").select("property_id").eq("user_id", user_id).execute()
        if not ga4_response.data:
            return jsonify({"error": "GA4 Property ID 없음"}), 404

        property_id = ga4_response.data[0]["property_id"]

        # 3. GA4 데이터 수집 (ga4_extractor_template.py 사용)
        extractor = GA4TemplateExtractor(property_id, CREDENTIALS_PATH)
        all_data = extractor.extract_data(days=30)

        ga4_data = {
            "summary": all_data.get("summary", {}),
            "pages": all_data.get("pages", []),
            "events": all_data.get("events", []),
            "transactions": all_data.get("transactions", []),
            "traffic_sources": all_data.get("traffic_sources", []),
            "info": all_data.get("info", {})
        }

        # 4. Supabase에 저장
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        result = save_ga4_data(user_id, str(start_date), str(end_date), ga4_data)

        return jsonify({
            "success": True,
            "message": "GA4 데이터 수집 완료",
            "user_id": user_id,
            "property_id": property_id,
            "data_id": result.get("id") if result else None
        })

    except Exception as e:
        print(f"Sync Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

# --- 유틸리티 포맷팅 함수 ---

def format_top_pages(pages):
    """상위 페이지 리스트를 문자열로 포맷팅"""
    result = []
    for i, page in enumerate(pages, 1):
        metrics = page.get("metrics", {})
        result.append(
            f"{i}. {page.get('pagePath', '알 수 없음')}\n"
            f"   조회수: {metrics.get('pageViews', 0):,.0f}회, 사용자: {metrics.get('activeUsers', 0):,.0f}명"
        )
    return "\n".join(result)

def format_traffic_sources(sources):
    """유입경로 리스트를 문자열로 포맷팅"""
    result = []
    for i, source in enumerate(sources, 1):
        result.append(
            f"{i}. {source.get('sessionSource', 'Direct')} / {source.get('sessionMedium', 'None')}\n"
            f"   사용자: {source.get('activeUsers', 0):,.0f}명, 세션: {source.get('sessions', 0):,.0f}개"
        )
    return "\n".join(result)

# --- 서버 실행부 ---

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 FrameFlow 로컬 API 서버를 시작합니다.")
    print(f"   - 주소: http://0.0.0.0:5000")
    print(f"   - 모드: Debug Mode (ON)")
    print("="*50 + "\n")
    
    # 로컬 테스트이므로 debug=True를 사용해 코드 수정 시 자동 재시작되게 함
    # host="0.0.0.0"은 외부 기기 접속을 허용함
    app.run(debug=True, host="0.0.0.0", port=5000)