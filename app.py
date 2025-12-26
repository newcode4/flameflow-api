from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import traceback
from telegram_bot import send_telegram_message

# 로컬 모듈
from supabase_client import (
    get_user_by_wp_id, 
    get_latest_ga4_data, 
    save_chat_history,
    update_token_balance,
    save_ga4_data
)
from ga4_extractor_template import GA4TemplateExtractor
from ga4_config import PROPERTY_ID, CREDENTIALS_PATH

load_dotenv()

app = Flask(__name__)
CORS(app)  # WordPress에서 호출 가능하도록

# Claude API 클라이언트
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.route("/")
def home():
    return jsonify({
        "service": "FrameFlow GA4 AI API",
        "version": "1.0",
        "status": "running"
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    AI 챗봇 엔드포인트
    
    Request:
    {
        "user_id": 1,           # Supabase user ID
        "question": "어제 방문자 몇 명?"
    }
    
    Response:
    {
        "answer": "어제는 247명이 방문했습니다.",
        "tokens_used": 150,
        "remaining_balance": 9850
    }
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        question = data.get("question")
        
        if not user_id or not question:
            return jsonify({"error": "user_id와 question 필수"}), 400
        
        # 1. 최근 GA4 데이터 조회
        ga4_data = get_latest_ga4_data(user_id)
        
        if not ga4_data:
            return jsonify({"error": "GA4 데이터가 없습니다. 먼저 연동하세요."}), 404
        
        # 2. Claude에게 컨텍스트 제공
        raw_data = ga4_data["raw_data"]
        
        # 요약 정보만 추출 (토큰 절약)
        context = f"""
당신은 GA4 데이터 분석 전문가입니다.

다음은 사용자의 GA4 데이터입니다:

[기간]
{raw_data['info']['date_range']['start']} ~ {raw_data['info']['date_range']['end']}

[전체 요약]
- 활성 사용자: {raw_data.get('summary', {}).get('activeUsers', 0):,}명
- 세션: {raw_data.get('summary', {}).get('sessions', 0):,}개
- 페이지뷰: {raw_data.get('summary', {}).get('screenPageViews', 0):,}회
- 총 수익: ₩{raw_data.get('summary', {}).get('purchaseRevenue', 0):,.0f}
- 거래: {raw_data.get('summary', {}).get('transactions', 0):,.0f}건
- 평균 세션 시간: {raw_data.get('summary', {}).get('averageSessionDuration', 0):.1f}초
- 이탈률: {raw_data.get('summary', {}).get('bounceRate', 0):.2%}

[상위 페이지 5개]
{format_top_pages(raw_data.get('pages', [])[:5])}

[유입경로 상위 5개]
{format_traffic_sources(raw_data.get('traffic_sources', [])[:5])}

사용자 질문에 짧고 명확하게 답변하세요. 숫자는 천 단위 쉼표로 표시하세요.
"""
        
        # 3. Claude API 호출
        response = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": context + f"\n\n질문: {question}"
                }
            ]
        )
        
        answer = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        
        # 4. 대화 기록 저장
        save_chat_history(user_id, question, answer, tokens_used)
        
        # 5. 토큰 차감 (입력+출력 합계)
        remaining_balance = update_token_balance(user_id, tokens_used)
        
        return jsonify({
            "answer": answer,
            "tokens_used": tokens_used,
            "remaining_balance": remaining_balance
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/ga4/sync", methods=["POST"])
def sync_ga4():
    """
    GA4 데이터 동기화
    
    Request:
    {
        "user_id": 1,
        "days": 30
    }
    """
    try:
        data = request.json
        user_id = data.get("user_id")
        days = data.get("days", 30)
        
        if not user_id:
            return jsonify({"error": "user_id 필수"}), 400
        
        # GA4 데이터 추출
        extractor = GA4TemplateExtractor(PROPERTY_ID, CREDENTIALS_PATH)
        all_data = extractor.extract_data(days)
        
        # 날짜 계산
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Supabase에 저장
        result = save_ga4_data(user_id, str(start_date), str(end_date), all_data)
        
        return jsonify({
            "status": "success",
            "data_id": result["id"],
            "api_calls": all_data["info"]["api_calls"],
            "summary": all_data.get("summary", {})
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 유틸리티 함수
def format_top_pages(pages):
    """상위 페이지 포맷팅"""
    result = []
    for i, page in enumerate(pages, 1):
        metrics = page.get("metrics", {})
        result.append(
            f"{i}. {page['pagePath']}\n"
            f"   방문: {metrics.get('pageViews', 0):,.0f}회, "
            f"사용자: {metrics.get('activeUsers', 0):,.0f}명"
        )
    return "\n".join(result)

def format_traffic_sources(sources):
    """유입경로 포맷팅"""
    result = []
    for i, source in enumerate(sources, 1):
        result.append(
            f"{i}. {source.get('sessionSource', 'N/A')} / {source.get('sessionMedium', 'N/A')}\n"
            f"   사용자: {source.get('activeUsers', 0):,.0f}명, "
            f"세션: {source.get('sessions', 0):,.0f}개"
        )
    return "\n".join(result)

if __name__ == "__main__":
    # 1. 환경변수 로드 확인
    print(f"Token Check: {os.getenv('TELEGRAM_BOT_TOKEN')[:5]}***") 
    
    try:
        # 2. 전송 시도
        send_telegram_message("🚀 서버 가동 테스트")
        
        # 3. 서버 실행
        app.run(debug=False, host="0.0.0.0", port=5000)
        
    except Exception as e:
        # 전송 실패 시 이유 출력
        print(f"‼️ 전송 중 에러 발생: {e}")

