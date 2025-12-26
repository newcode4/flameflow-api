from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, OrderBy
)
import json
from datetime import datetime, timedelta
from collections import defaultdict
import time

# 설정 파일 import
from ga4_config import *

class GA4TemplateExtractor:
    """
    GA4 데이터 추출기 (템플릿)
    
    ga4_config.py에서 설정 변경
    """
    
    def __init__(self, property_id=None, credentials_path=None):
        self.property_id = property_id or PROPERTY_ID
        self.credentials_path = credentials_path or CREDENTIALS_PATH
        self.client = BetaAnalyticsDataClient.from_service_account_json(
            self.credentials_path
        )
        self.errors = []
        self.api_calls = 0
    
    def get_date_range(self, days=None):
        """날짜 범위 생성"""
        days = days or DEFAULT_DAYS
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days-1)
        return {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "days": days
        }
    
    def run_report(self, name, dimensions, metrics, date_range, 
                   limit=None, order_by=None, retry=True):
        """
        안전한 API 호출
        
        Args:
            name: 리포트 이름
            dimensions: 차원 리스트
            metrics: 측정항목 리스트
            date_range: 날짜 범위
            limit: 최대 행 수
            order_by: 정렬 (dict or list)
            retry: 재시도 여부
        """
        self.api_calls += 1
        
        for attempt in range(API_STRATEGY["retry_count"]):
            try:
                # 정렬 설정
                order_bys = []
                if order_by:
                    orders = order_by if isinstance(order_by, list) else [order_by]
                    for order in orders:
                        order_bys.append(OrderBy(
                            metric=OrderBy.MetricOrderBy(metric_name=order["metric"]),
                            desc=order.get("desc", True)
                        ))
                
                request = RunReportRequest(
                    property=f"properties/{self.property_id}",
                    dimensions=[Dimension(name=d) for d in dimensions],
                    metrics=[Metric(name=m) for m in metrics],
                    date_ranges=[DateRange(
                        start_date=date_range["start"],
                        end_date=date_range["end"]
                    )],
                    limit=limit,
                    order_bys=order_bys if order_bys else None
                )
                
                response = self.client.run_report(request)
                rows = len(response.rows) if response else 0
                print(f"   ✅ {name}: {rows}행")
                return response
                
            except Exception as e:
                error_msg = f"{name}: {str(e)[:150]}"
                
                if attempt < API_STRATEGY["retry_count"] - 1 and retry:
                    print(f"   ⚠️  {error_msg}")
                    print(f"   🔄 재시도 {attempt + 1}/{API_STRATEGY['retry_count']}")
                    time.sleep(API_STRATEGY["retry_delay"])
                else:
                    self.errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
                    return None
    
    def extract_data(self, days=None):
        """
        설정 기반 데이터 추출
        
        ga4_config.py의 EXTRACT_CONFIG에서 on/off
        """
        date_range = self.get_date_range(days)
        self.errors = []
        self.api_calls = 0
        
        print(f"\n{'='*70}")
        print(f"🚀 GA4 데이터 추출 (템플릿)")
        print(f"{'='*70}")
        print(f"📅 {date_range['start']} ~ {date_range['end']} ({date_range['days']}일)")
        print(f"\n{'='*70}\n")
        
        result = {
            "info": {
                "property_id": self.property_id,
                "date_range": date_range,
                "extracted_at": datetime.now().isoformat(),
                "version": "9.0-template",
                "config": EXTRACT_CONFIG,
                "api_calls": 0,
                "errors": []
            }
        }
        
        # ========== 1. 전체 요약 ==========
        if EXTRACT_CONFIG["summary"]:
            print("📊 1. 전체 요약")
            result["summary"] = self._extract_summary(date_range)
        
        # ========== 2. 페이지 데이터 ==========
        if EXTRACT_CONFIG["pages"]:
            print("\n📄 2. 페이지 데이터")
            result["pages"] = self._extract_pages(date_range)
        
        # ========== 3. 이벤트 데이터 ==========
        if EXTRACT_CONFIG["events"]:
            print("\n🎯 3. 이벤트 데이터")
            result["events"] = self._extract_events(date_range)
            result["key_events"] = self._extract_key_events(date_range)
        
        # ========== 4. 거래 데이터 ==========
        if EXTRACT_CONFIG["transactions"]:
            print("\n💳 4. 거래 데이터")
            result["transactions"] = self._extract_transactions(date_range)
        
        # ========== 5. 유입경로 ==========
        if EXTRACT_CONFIG["traffic_sources"]:
            print("\n🚪 5. 유입경로")
            result["traffic_sources"] = self._extract_sources(date_range)
        
        # ========== 6. 캠페인 ==========
        if EXTRACT_CONFIG["campaigns"]:
            print("\n📣 6. 캠페인")
            result["campaigns"] = self._extract_campaigns(date_range)
        
        # ========== 7. 기기 ==========
        if EXTRACT_CONFIG["devices"]:
            print("\n💻 7. 기기")
            result["devices"] = self._extract_devices(date_range)
        
        # ========== 8. 위치 ==========
        if EXTRACT_CONFIG["locations"]:
            print("\n🌍 8. 위치")
            result["locations"] = self._extract_locations(date_range)
        
        # ========== 9. 콘텐츠 ==========
        if EXTRACT_CONFIG["content"]:
            print("\n📝 9. 콘텐츠")
            result["content_groups"] = self._extract_content(date_range)
        
        # ========== 10. 시간 분석 ==========
        if EXTRACT_CONFIG["daily_trend"]:
            print("\n📈 10. 일별 트렌드")
            result["daily_trend"] = self._extract_daily(date_range)
        
        if EXTRACT_CONFIG["hourly_traffic"]:
            print("\n⏰ 11. 시간대별")
            result["hourly_traffic"] = self._extract_hourly(date_range)
        
        if EXTRACT_CONFIG["day_of_week"]:
            print("\n📅 12. 요일별")
            result["day_of_week"] = self._extract_day_of_week(date_range)
        
        # ========== 13. 사용자 분석 ==========
        if EXTRACT_CONFIG["new_vs_returning"]:
            print("\n👤 13. 신규/재방문")
            result["new_vs_returning"] = self._extract_new_vs_returning(date_range)
        
        if EXTRACT_CONFIG["user_segments"]:
            print("\n🎯 14. 사용자 세그먼트")
            result["user_segments"] = self._extract_user_segments(date_range)
        
        # ========== 15. 행동 분석 ==========
        if EXTRACT_CONFIG["search_terms"]:
            print("\n🔍 15. 검색어")
            result["search_terms"] = self._extract_search_terms(date_range)
        
        if EXTRACT_CONFIG["scroll_depth"]:
            print("\n📜 16. 스크롤")
            result["scroll_depth"] = self._extract_scroll(date_range)
        
        if EXTRACT_CONFIG["engagement"]:
            print("\n💪 17. 참여도")
            result["engagement"] = self._extract_engagement(date_range)
        
        # ========== 18. 전환 퍼널 ==========
        if EXTRACT_CONFIG["conversion_funnel"]:
            print("\n🛒 18. 전환 퍼널")
            result["conversion_funnel"] = self._calculate_funnel(result)
        
        # 최종 정보 업데이트
        result["info"]["api_calls"] = self.api_calls
        result["info"]["errors"] = self.errors
        
        print(f"\n✅ 추출 완료!")
        print(f"📞 총 API 호출: {self.api_calls}회")
        print(f"⚠️  에러: {len(self.errors)}건")
        
        return result
    
    # ========== 개별 추출 메서드 ==========
    
    def _extract_summary(self, date_range):
        """전체 요약"""
        response = self.run_report(
            "전체 요약",
            [],
            [
                DEFAULT_METRICS["users"],
                DEFAULT_METRICS["sessions"],
                DEFAULT_METRICS["pageviews"],
                DEFAULT_METRICS["events"],
                DEFAULT_METRICS["revenue"],
                DEFAULT_METRICS["transactions"],
                "newUsers",
                "averageSessionDuration",
                DEFAULT_METRICS["bounceRate"],
            ],
            date_range
        )
        return self._parse_single(response)
    
    def _extract_pages(self, date_range):
        """페이지 데이터"""
        # 기본 지표
        metrics = self.run_report(
            "페이지 기본",
            [DEFAULT_DIMENSIONS["page"]],
            [
                DEFAULT_METRICS["pageviews"],
                DEFAULT_METRICS["users"],
                "newUsers",
                "averageSessionDuration",
                DEFAULT_METRICS["bounceRate"],
                "engagementRate",
                DEFAULT_METRICS["events"],
            ],
            date_range,
            LIMITS["pages"],
            {"metric": DEFAULT_METRICS["pageviews"], "desc": True}
        )
        
        # 페이지별 이벤트
        events = self.run_report(
            "페이지별 이벤트",
            [DEFAULT_DIMENSIONS["page"], DEFAULT_DIMENSIONS["event"]],
            ["eventCount"],
            date_range,
            LIMITS["pages"] * 5
        )
        
        # 페이지별 유입경로
        sources = self.run_report(
            "페이지별 유입",
            [DEFAULT_DIMENSIONS["page"], DEFAULT_DIMENSIONS["source"], DEFAULT_DIMENSIONS["medium"]],
            [DEFAULT_METRICS["users"], DEFAULT_METRICS["sessions"]],
            date_range,
            LIMITS["pages"] * 5
        )
        
        # 페이지별 기기
        devices = self.run_report(
            "페이지별 기기",
            [DEFAULT_DIMENSIONS["page"], DEFAULT_DIMENSIONS["device"]],
            [DEFAULT_METRICS["users"]],
            date_range,
            LIMITS["pages"] * 3
        )
        
        return self._unify_pages(metrics, events, sources, devices)
    
    def _extract_events(self, date_range):
        """전체 이벤트"""
        response = self.run_report(
            "전체 이벤트",
            [DEFAULT_DIMENSIONS["event"]],
            ["eventCount", DEFAULT_METRICS["users"]],
            date_range,
            LIMITS["events"],
            {"metric": "eventCount", "desc": True}
        )
        return self._parse_multi(response)
    
    def _extract_key_events(self, date_range):
        """주요 이벤트 상세"""
        key_events = {}
        
        for event in KEY_EVENTS:
            # 이벤트별 페이지
            response = self.run_report(
                f"{event} 상세",
                [CUSTOM_DIMENSIONS["page_location"]],
                ["eventCount"],
                date_range,
                50
            )
            key_events[event] = self._parse_multi(response)
        
        return key_events
    
    def _extract_transactions(self, date_range):
        """거래 데이터"""
        # 거래 기본
        basic = self.run_report(
            "거래 기본",
            [CUSTOM_DIMENSIONS["transaction_id"]],
            [DEFAULT_METRICS["revenue"], "eventCount"],
            date_range,
            LIMITS["transactions"]
        )
        
        # 거래 맞춤 정보
        custom = self.run_report(
            "거래 맞춤",
            [
                CUSTOM_DIMENSIONS["transaction_id"],
                CUSTOM_DIMENSIONS["payment_type"],
            ],
            [DEFAULT_METRICS["revenue"]],
            date_range,
            LIMITS["transactions"]
        )
        
        # 거래별 유입경로
        sources = self.run_report(
            "거래 유입",
            [
                CUSTOM_DIMENSIONS["transaction_id"],
                DEFAULT_DIMENSIONS["source"],
                DEFAULT_DIMENSIONS["medium"]
            ],
            [DEFAULT_METRICS["revenue"]],
            date_range,
            LIMITS["transactions"]
        )
        
        return self._merge_transactions(basic, custom, sources)
    
    def _extract_sources(self, date_range):
        """유입경로"""
        response = self.run_report(
            "유입경로",
            [DEFAULT_DIMENSIONS["source"], DEFAULT_DIMENSIONS["medium"]],
            [
                DEFAULT_METRICS["users"],
                DEFAULT_METRICS["sessions"],
                DEFAULT_METRICS["events"],
                DEFAULT_METRICS["revenue"],
                DEFAULT_METRICS["transactions"],
            ],
            date_range,
            LIMITS["sources"],
            {"metric": DEFAULT_METRICS["users"], "desc": True}
        )
        return self._parse_multi(response)
    
    def _extract_campaigns(self, date_range):
        """캠페인"""
        response = self.run_report(
            "캠페인",
            [
                CUSTOM_DIMENSIONS["campaign"],
                CUSTOM_DIMENSIONS["utm_source"],
                CUSTOM_DIMENSIONS["utm_medium"]
            ],
            [
                DEFAULT_METRICS["sessions"],
                DEFAULT_METRICS["events"],
                DEFAULT_METRICS["revenue"]
            ],
            date_range,
            LIMITS["campaigns"]
        )
        return self._parse_multi(response)
    
    def _extract_devices(self, date_range):
        """기기"""
        response = self.run_report(
            "기기",
            [DEFAULT_DIMENSIONS["device"], "operatingSystem", "browser"],
            [
                DEFAULT_METRICS["users"],
                DEFAULT_METRICS["sessions"],
                DEFAULT_METRICS["events"],
                DEFAULT_METRICS["transactions"]
            ],
            date_range,
            LIMITS["devices"]
        )
        return self._parse_multi(response)
    
    def _extract_locations(self, date_range):
        """위치"""
        response = self.run_report(
            "위치",
            ["country", DEFAULT_DIMENSIONS["city"]],
            [DEFAULT_METRICS["users"], DEFAULT_METRICS["sessions"]],
            date_range,
            LIMITS["locations"]
        )
        return self._parse_multi(response)
    
    def _extract_content(self, date_range):
        """콘텐츠 그룹"""
        response = self.run_report(
            "콘텐츠 그룹",
            [CUSTOM_DIMENSIONS["content_group"]],
            [DEFAULT_METRICS["pageviews"], DEFAULT_METRICS["users"]],
            date_range,
            100
        )
        return self._parse_multi(response)
    
    def _extract_daily(self, date_range):
        """일별 트렌드"""
        response = self.run_report(
            "일별",
            [DEFAULT_DIMENSIONS["date"]],
            [
                DEFAULT_METRICS["users"],
                DEFAULT_METRICS["sessions"],
                DEFAULT_METRICS["events"],
                DEFAULT_METRICS["revenue"],
                DEFAULT_METRICS["transactions"]
            ],
            date_range
        )
        return self._parse_multi(response)
    
    def _extract_hourly(self, date_range):
        """시간대별"""
        response = self.run_report(
            "시간대별",
            [DEFAULT_DIMENSIONS["hour"]],
            [DEFAULT_METRICS["users"], DEFAULT_METRICS["sessions"]],
            date_range
        )
        return self._parse_multi(response)
    
    def _extract_day_of_week(self, date_range):
        """요일별"""
        response = self.run_report(
            "요일별",
            ["dayOfWeek"],
            [DEFAULT_METRICS["users"], DEFAULT_METRICS["sessions"]],
            date_range
        )
        return self._parse_multi(response)
    
    def _extract_new_vs_returning(self, date_range):
        """신규/재방문"""
        response = self.run_report(
            "신규/재방문",
            ["newVsReturning"],
            [
                DEFAULT_METRICS["users"],
                DEFAULT_METRICS["sessions"],
                DEFAULT_METRICS["events"],
                DEFAULT_METRICS["transactions"]
            ],
            date_range
        )
        return self._parse_multi(response)
    
    def _extract_user_segments(self, date_range):
        """사용자 세그먼트"""
        if "user_type" not in CUSTOM_DIMENSIONS:
            return []
        
        response = self.run_report(
            "사용자 세그먼트",
            [CUSTOM_DIMENSIONS["user_type"]],
            [
                DEFAULT_METRICS["users"],
                DEFAULT_METRICS["sessions"],
                DEFAULT_METRICS["revenue"]
            ],
            date_range,
            50
        )
        return self._parse_multi(response)
    
    def _extract_search_terms(self, date_range):
        """검색어"""
        response = self.run_report(
            "검색어",
            [CUSTOM_DIMENSIONS["search_term"]],
            ["eventCount"],
            date_range,
            LIMITS["search_terms"]
        )
        return self._parse_multi(response)
    
    def _extract_scroll(self, date_range):
        """스크롤 깊이"""
        response = self.run_report(
            "스크롤",
            [CUSTOM_DIMENSIONS["scroll_depth"]],
            ["eventCount"],
            date_range,
            50
        )
        return self._parse_multi(response)
    
    def _extract_engagement(self, date_range):
        """참여도"""
        response = self.run_report(
            "참여도",
            [],
            [
                "engagementRate",
                "userEngagementDuration",
                "averageSessionDuration",
                "sessionsPerUser"
            ],
            date_range
        )
        return self._parse_single(response)
    
    # ========== 유틸리티 메서드 ==========
    
    def _unify_pages(self, metrics, events, sources, devices):
        """페이지 통합"""
        pages_dict = defaultdict(lambda: {
            "metrics": {},
            "events": {},
            "traffic_sources": {},
            "devices": {}
        })
        
        # 기본 지표
        if metrics:
            for row in metrics.rows:
                page = row.dimension_values[0].value
                pages_dict[page]["metrics"] = {
                    "pageViews": float(row.metric_values[0].value),
                    "activeUsers": float(row.metric_values[1].value),
                    "newUsers": float(row.metric_values[2].value),
                    "avgSessionDuration": float(row.metric_values[3].value),
                    "bounceRate": float(row.metric_values[4].value),
                    "engagementRate": float(row.metric_values[5].value),
                    "keyEvents": float(row.metric_values[6].value)
                }
        
        # 이벤트
        if events:
            for row in events.rows:
                page = row.dimension_values[0].value
                event = row.dimension_values[1].value
                count = float(row.metric_values[0].value)
                pages_dict[page]["events"][event] = count
        
        # 유입경로
        if sources:
            for row in sources.rows:
                page = row.dimension_values[0].value
                source = row.dimension_values[1].value
                medium = row.dimension_values[2].value
                users = float(row.metric_values[0].value)
                sessions = float(row.metric_values[1].value)
                key = f"{source}/{medium}"
                pages_dict[page]["traffic_sources"][key] = {
                    "users": users,
                    "sessions": sessions
                }
        
        # 기기
        if devices:
            for row in devices.rows:
                page = row.dimension_values[0].value
                device = row.dimension_values[1].value
                users = float(row.metric_values[0].value)
                pages_dict[page]["devices"][device] = users
        
        result = []
        for page_path, data in pages_dict.items():
            result.append({"pagePath": page_path, **data})
        
        result.sort(key=lambda x: x.get("metrics", {}).get("pageViews", 0), reverse=True)
        return result
    
    def _merge_transactions(self, basic, custom, sources):
        """거래 통합"""
        merged = {}
        
        if basic:
            for row in basic.rows:
                tid = row.dimension_values[0].value
                merged[tid] = {
                    "transaction_id": tid,
                    "revenue": float(row.metric_values[0].value),
                    "count": float(row.metric_values[1].value)
                }
        
        if custom:
            for row in custom.rows:
                tid = row.dimension_values[0].value
                if tid in merged:
                    merged[tid]["payment_type"] = row.dimension_values[1].value
        
        if sources:
            for row in sources.rows:
                tid = row.dimension_values[0].value
                if tid in merged:
                    source = row.dimension_values[1].value
                    medium = row.dimension_values[2].value
                    merged[tid]["traffic_source"] = f"{source}/{medium}"
        
        result = list(merged.values())
        result.sort(key=lambda x: x.get("revenue", 0), reverse=True)
        return result
    
    def _calculate_funnel(self, data):
        """퍼널 계산"""
        events = {e["eventName"]: e["eventCount"] 
                  for e in data.get("events", [])}
        
        funnel = {
            "page_views": events.get("page_view", 0),
            "scrolls": events.get("scroll", 0),
            "form_starts": events.get("form_start", 0),
            "form_submits": events.get("form_submit", 0),
            "purchases": events.get("purchase", 0),
        }
        
        # 전환율
        if funnel["page_views"] > 0:
            funnel["scroll_rate"] = funnel["scrolls"] / funnel["page_views"]
            funnel["form_rate"] = funnel["form_starts"] / funnel["page_views"]
        
        if funnel["form_starts"] > 0:
            funnel["submit_rate"] = funnel["form_submits"] / funnel["form_starts"]
        
        if funnel["form_submits"] > 0:
            funnel["purchase_rate"] = funnel["purchases"] / funnel["form_submits"]
        
        return funnel
    
    def _parse_single(self, response):
        """단일 행 파싱"""
        if not response or not response.rows:
            return {}
        
        row = response.rows[0]
        result = {}
        
        for i, metric in enumerate(response.metric_headers):
            try:
                result[metric.name] = float(row.metric_values[i].value)
            except:
                result[metric.name] = row.metric_values[i].value
        
        return result
    
    def _parse_multi(self, response):
        """여러 행 파싱"""
        if not response or not response.rows:
            return []
        
        results = []
        for row in response.rows:
            item = {}
            for i, dim in enumerate(response.dimension_headers):
                item[dim.name] = row.dimension_values[i].value
            for i, metric in enumerate(response.metric_headers):
                try:
                    item[metric.name] = float(row.metric_values[i].value)
                except:
                    item[metric.name] = row.metric_values[i].value
            results.append(item)
        
        return results
    
    def print_validation(self, data):
        """검증 출력"""
        print(f"\n{'='*70}")
        print(f"📊 데이터 검증")
        print(f"{'='*70}")
        
        info = data.get("info", {})
        summary = data.get("summary", {})
        
        print(f"\n📅 수집 정보:")
        print(f"   기간: {info['date_range']['start']} ~ {info['date_range']['end']}")
        print(f"   API 호출: {info['api_calls']}회")
        print(f"   에러: {len(info['errors'])}건")
        
        if summary:
            print(f"\n💰 전체 요약:")
            print(f"   활성 사용자: {summary.get('activeUsers', 0):,.0f}")
            print(f"   세션: {summary.get('sessions', 0):,.0f}")
            print(f"   총 수익: ₩{summary.get('purchaseRevenue', 0):,.0f}")
            print(f"   거래: {summary.get('transactions', 0):,.0f}건")
        
        print(f"\n📦 수집 데이터:")
        for key, value in data.items():
            if key not in ["info", "summary"] and isinstance(value, list):
                print(f"   {key}: {len(value)}개")
        
        if info.get("errors"):
            print(f"\n⚠️  에러:")
            for err in info["errors"][:3]:
                print(f"   - {err}")
        
        print(f"\n{'='*70}\n")


# 실행
if __name__ == "__main__":
    print("\n" + "🔥"*35)
    print("   GA4 템플릿 추출기 v9.0")
    print("🔥"*35 + "\n")
    
    extractor = GA4TemplateExtractor()
    data = extractor.extract_data(days=30)
    
    # 검증
    extractor.print_validation(data)
    
    # 저장
    output_file = f"ga4_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 저장: {output_file}\n")