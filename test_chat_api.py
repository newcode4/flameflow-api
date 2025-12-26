import requests

# 테스트 1: 기본 질문
print("=== 테스트 1: 전체 요약 ===")
response = requests.post("http://localhost:5000/api/chat", json={
    "user_id": 1,
    "question": "지난 30일 동안 활성 사용자가 몇 명이야?"
})
print(response.json())

print("\n=== 테스트 2: 수익 질문 ===")
response = requests.post("http://localhost:5000/api/chat", json={
    "user_id": 1,
    "question": "총 수익이 얼마야?"
})
print(response.json())

print("\n=== 테스트 3: 비교 질문 ===")
response = requests.post("http://localhost:5000/api/chat", json={
    "user_id": 1,
    "question": "가장 많이 방문한 페이지 3개 알려줘"
})
print(response.json())