"""
AI 챗봇 서비스
사용자 데이터 기반 AI 대화 처리
"""
import anthropic
from typing import Dict, List, Optional
from database.supabase_client import db
from config.settings import get_config
from utils.logger import app_logger, error_logger

config = get_config()

# Claude API 클라이언트 초기화
claude = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

class ChatService:
    """AI 챗봇 서비스"""

    @staticmethod
    def build_context(user_id: int) -> Optional[str]:
        """
        사용자별 AI 컨텍스트 생성
        - 사용자의 비즈니스 정보
        - GA4 데이터 요약
        - KPI 및 목표
        """
        try:
            # 사용자 프로필 조회
            user = db.get_user_by_id(user_id)
            if not user:
                return None

            user_context = user.get("user_context") or {}

            # GA4 데이터 조회
            ga4_data = db.get_latest_ga4_data(user_id)
            if not ga4_data:
                return "사용자의 GA4 데이터가 없습니다. 먼저 데이터 동기화를 진행하세요."

            raw_data = ga4_data["raw_data"]
            summary = raw_data.get("summary", {})

            # 컨텍스트 구성
            context = f"""
당신은 GA4 데이터 분석 전문 AI 어시스턴트입니다.

[사용자 정보]
- 이메일: {user.get('email')}
- 플랜: {user.get('plan')}
"""

            # 사용자가 입력한 AI 학습 정보
            if user_context:
                context += f"""
[비즈니스 정보]
- 비즈니스 유형: {user_context.get('business_type', '정보 없음')}
- 핵심 KPI: {', '.join(user_context.get('kpi', []))}
- 목표: {user_context.get('goals', '정보 없음')}
- 타겟 고객: {user_context.get('target_audience', '정보 없음')}
- 추가 정보: {user_context.get('additional_info', '없음')}
"""

            # GA4 데이터 요약
            context += f"""
[분석 기간]
{raw_data['info']['date_range']['start']} ~ {raw_data['info']['date_range']['end']}

[핵심 지표 요약]
- 활성 사용자: {summary.get('activeUsers', 0):,}명
- 세션: {summary.get('sessions', 0):,}개
- 페이지뷰: {summary.get('screenPageViews', 0):,}회
- 총 수익: ₩{summary.get('purchaseRevenue', 0):,.0f}
- 거래 수: {summary.get('transactions', 0):,.0f}건
- 이탈률: {summary.get('bounceRate', 0):.2%}

[인기 페이지 상위 5개]
{ChatService._format_pages(raw_data.get('pages', [])[:5])}

[주요 유입경로 상위 5개]
{ChatService._format_traffic_sources(raw_data.get('traffic_sources', [])[:5])}

사용자의 질문에 대해 위 데이터를 기반으로 명확하고 실용적인 조언을 제공하세요.
숫자는 가독성을 위해 천 단위 쉼표(,)를 사용하세요.
"""

            return context

        except Exception as e:
            error_logger.error(f"Error building context: {e}")
            return None

    @staticmethod
    def _format_pages(pages: List[Dict]) -> str:
        """페이지 데이터 포맷팅"""
        result = []
        for i, page in enumerate(pages, 1):
            metrics = page.get("metrics", {})
            result.append(
                f"{i}. {page.get('pagePath', '알 수 없음')}\n"
                f"   조회수: {metrics.get('pageViews', 0):,.0f}회, "
                f"사용자: {metrics.get('activeUsers', 0):,.0f}명"
            )
        return "\n".join(result) if result else "데이터 없음"

    @staticmethod
    def _format_traffic_sources(sources: List[Dict]) -> str:
        """유입경로 데이터 포맷팅"""
        result = []
        for i, source in enumerate(sources, 1):
            result.append(
                f"{i}. {source.get('sessionSource', 'Direct')} / "
                f"{source.get('sessionMedium', 'None')}\n"
                f"   사용자: {source.get('activeUsers', 0):,.0f}명, "
                f"세션: {source.get('sessions', 0):,.0f}개"
            )
        return "\n".join(result) if result else "데이터 없음"

    @staticmethod
    def chat(user_id: int, question: str, include_history: bool = True) -> Dict:
        """
        AI 챗봇과 대화

        Args:
            user_id: 사용자 ID
            question: 질문
            include_history: 대화 히스토리 포함 여부

        Returns:
            {"success": bool, "answer": str, "tokens_used": int, "remaining_balance": int}
        """
        try:
            # 토큰 잔액 확인
            user = db.get_user_by_id(user_id)
            if not user or user["token_balance"] <= 0:
                return {
                    "success": False,
                    "message": "토큰 잔액이 부족합니다. 토큰을 충전해주세요."
                }

            # 컨텍스트 구성
            context = ChatService.build_context(user_id)
            if not context:
                return {
                    "success": False,
                    "message": "사용자 컨텍스트를 불러올 수 없습니다."
                }

            # 대화 히스토리 추가 (선택적)
            messages = []

            if include_history:
                history = db.get_chat_history(user_id, limit=5)
                for chat in reversed(history):  # 시간순 정렬
                    messages.append({
                        "role": "user",
                        "content": chat["question"]
                    })
                    messages.append({
                        "role": "assistant",
                        "content": chat["answer"]
                    })

            # 현재 질문 추가
            messages.append({
                "role": "user",
                "content": context + f"\n\n[사용자 질문]\n{question}"
            })

            # Claude API 호출
            response = claude.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=config.CLAUDE_MAX_TOKENS,
                messages=messages
            )

            answer = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            # 대화 기록 저장
            db.save_chat_history(user_id, question, answer, tokens_used)

            # 토큰 차감
            remaining_balance = db.update_token_balance(user_id, tokens_used)

            app_logger.info(
                f"Chat completed: user_id={user_id}, tokens_used={tokens_used}, "
                f"remaining={remaining_balance}"
            )

            return {
                "success": True,
                "answer": answer,
                "tokens_used": tokens_used,
                "remaining_balance": remaining_balance
            }

        except Exception as e:
            error_logger.error(f"Error in chat: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_chat_history(user_id: int, limit: int = 20) -> List[Dict]:
        """대화 히스토리 조회"""
        try:
            return db.get_chat_history(user_id, limit)
        except Exception as e:
            error_logger.error(f"Error getting chat history: {e}")
            return []
