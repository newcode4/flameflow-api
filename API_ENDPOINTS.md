# FrameFlow API 엔드포인트 가이드

## 📋 MVP 핵심 엔드포인트 (2025-12-27 추가)

### 1️⃣ 사용자 등록
**WordPress 회원가입 시 자동 호출**

```http
POST /api/user/register
Content-Type: application/json

{
  "wp_user_id": 123,
  "email": "user@example.com",
  "property_id": "488770841"
}
```

**응답:**
```json
{
  "success": true,
  "user_id": 5,
  "message": "사용자 등록 완료"
}
```

**동작:**
- `users` 테이블에 사용자 생성 (초기 토큰 10만개)
- `ga4_accounts` 테이블에 Property ID 저장
- 공통 service-account 사용

---

### 2️⃣ 사용자 조회
**WordPress ID로 Supabase 사용자 정보 찾기**

```http
POST /api/user/get-by-wp-id
Content-Type: application/json

{
  "wp_user_id": 123
}
```

**응답:**
```json
{
  "success": true,
  "user": {
    "id": 5,
    "wp_user_id": 123,
    "email": "user@example.com",
    "token_balance": 100000,
    "created_at": "2025-12-27T10:00:00"
  }
}
```

**사용 시나리오:**
- WordPress 로그인 시 Supabase user_id 찾기
- 토큰 잔액 확인
- 사용자 정보 표시

---

### 3️⃣ GA4 데이터 수집
**버튼 클릭 시 GA4 데이터 가져오기**

```http
POST /api/ga4/sync-user
Content-Type: application/json

{
  "wp_user_id": 123
}
```

**응답:**
```json
{
  "success": true,
  "message": "GA4 데이터 수집 완료",
  "user_id": 5,
  "property_id": "488770841",
  "data_id": 42
}
```

**동작:**
1. wp_user_id → user_id 변환
2. user_id → property_id 조회
3. GA4 API 호출 (최근 30일 데이터)
4. Supabase `ga4_data` 테이블에 저장

**수집 데이터:**
- 요약 지표 (방문자, 세션, 페이지뷰, 수익 등)
- 인기 페이지
- 이벤트
- 거래 내역
- 트래픽 소스

---

## 🔄 기존 엔드포인트

### 4️⃣ AI 챗봇 대화

```http
POST /api/chat
Content-Type: application/json

{
  "user_id": 5,
  "question": "어제 방문자 몇 명?"
}
```

**응답:**
```json
{
  "answer": "어제 방문자는 1,234명입니다...",
  "tokens_used": 523,
  "remaining_balance": 99477
}
```

---

### 5️⃣ 전체 GA4 동기화

```http
POST /api/ga4/sync
Content-Type: application/json

{
  "user_id": 5,
  "days": 30
}
```

---

## 🧪 테스트 방법

### Postman / Insomnia

```bash
# 1. 사용자 등록
POST http://localhost:5000/api/user/register
{
  "wp_user_id": 999,
  "email": "test@example.com",
  "property_id": "488770841"
}

# 2. 사용자 조회
POST http://localhost:5000/api/user/get-by-wp-id
{
  "wp_user_id": 999
}

# 3. GA4 데이터 수집
POST http://localhost:5000/api/ga4/sync-user
{
  "wp_user_id": 999
}
```

### cURL

```bash
# 1. 사용자 등록
curl -X POST http://localhost:5000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{"wp_user_id": 999, "email": "test@example.com", "property_id": "488770841"}'

# 2. 사용자 조회
curl -X POST http://localhost:5000/api/user/get-by-wp-id \
  -H "Content-Type: application/json" \
  -d '{"wp_user_id": 999}'

# 3. GA4 데이터 수집
curl -X POST http://localhost:5000/api/ga4/sync-user \
  -H "Content-Type: application/json" \
  -d '{"wp_user_id": 999}'
```

---

## 🌐 WordPress 연동 예시

### PHP (functions.php)

```php
<?php
// 1. 회원가입 시 FrameFlow 등록
add_action('user_register', 'register_frameflow_user');
function register_frameflow_user($user_id) {
    $user = get_userdata($user_id);

    $response = wp_remote_post('http://your-server:5000/api/user/register', [
        'headers' => ['Content-Type' => 'application/json'],
        'body' => json_encode([
            'wp_user_id' => $user_id,
            'email' => $user->user_email,
            'property_id' => get_user_meta($user_id, 'ga4_property_id', true)
        ])
    ]);

    if (!is_wp_error($response)) {
        $data = json_decode(wp_remote_retrieve_body($response), true);
        if ($data['success']) {
            update_user_meta($user_id, 'frameflow_user_id', $data['user_id']);
        }
    }
}

// 2. 마이페이지에서 GA4 데이터 수집
function fetch_ga4_data() {
    $wp_user_id = get_current_user_id();

    $response = wp_remote_post('http://your-server:5000/api/ga4/sync-user', [
        'headers' => ['Content-Type' => 'application/json'],
        'body' => json_encode(['wp_user_id' => $wp_user_id])
    ]);

    if (!is_wp_error($response)) {
        $data = json_decode(wp_remote_retrieve_body($response), true);
        return $data;
    }

    return null;
}
?>
```

### JavaScript (AJAX)

```javascript
// 1. 사용자 조회
async function getFrameFlowUser(wpUserId) {
  const response = await fetch('http://your-server:5000/api/user/get-by-wp-id', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ wp_user_id: wpUserId })
  });

  const data = await response.json();
  if (data.success) {
    console.log('토큰 잔액:', data.user.token_balance);
    return data.user;
  }
}

// 2. GA4 데이터 수집 버튼
document.getElementById('fetch-ga4-btn').addEventListener('click', async () => {
  const wpUserId = <?php echo get_current_user_id(); ?>;

  // 로딩 표시
  document.getElementById('loading').style.display = 'block';

  try {
    const response = await fetch('http://your-server:5000/api/ga4/sync-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ wp_user_id: wpUserId })
    });

    const data = await response.json();

    if (data.success) {
      alert('GA4 데이터 수집 완료!');
      location.reload();
    } else {
      alert('에러: ' + data.error);
    }
  } catch (error) {
    alert('연결 실패: ' + error.message);
  } finally {
    document.getElementById('loading').style.display = 'none';
  }
});
```

---

## 🔒 보안 고려사항

### 1. CORS 설정
현재는 모든 도메인 허용 (`CORS(app)`). 프로덕션에서는 WordPress 도메인만 허용:

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-wordpress-site.com"]
    }
})
```

### 2. API 키 인증 (선택)
민감한 엔드포인트는 API 키 추가:

```python
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_SECRET_KEY'):
            return jsonify({'error': '인증 실패'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/ga4/sync-user', methods=['POST'])
@require_api_key
def sync_user_ga4():
    # ...
```

---

## 📊 에러 처리

### 일반적인 에러 응답

```json
{
  "error": "에러 메시지"
}
```

### HTTP 상태 코드
- `200` - 성공
- `400` - 잘못된 요청 (필수 필드 누락)
- `404` - 사용자/데이터 없음
- `500` - 서버 에러

---

## 🚀 배포 후 URL 변경

로컬: `http://localhost:5000`
서버: `http://your-vultr-ip:5000`

WordPress에서 URL을 환경변수로 관리:
```php
define('FRAMEFLOW_API_URL', 'http://your-server:5000');
```

---

**FrameFlow API v2.0 - WordPress 통합 준비 완료** ✨
