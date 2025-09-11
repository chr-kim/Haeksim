# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_evaluate_endpoint_success():
    """정상적인 평가 요청 테스트"""
    response = client.post(
        "/evaluate",
        json={
            "problem_id": 101,
            "user_answer_id": 1,
            "user_reasoning": "지문을 분석한 결과 1번이 정답입니다."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_score" in data
    assert "feedbacks" in data

def test_evaluate_endpoint_validation_error():
    """잘못된 요청 데이터 테스트"""
    response = client.post(
        "/evaluate",
        json={
            "problem_id": "invalid",  # 숫자가 아닌 값
            "user_answer_id": 1,
            "user_reasoning": "테스트"
        }
    )
    assert response.status_code == 422  # 유효성 검사 오류

def test_evaluate_endpoint_missing_pdf():
    """존재하지 않는 문제 ID 테스트"""
    response = client.post(
        "/evaluate",
        json={
            "problem_id": 99999,  # 존재하지 않는 문제
            "user_answer_id": 1,
            "user_reasoning": "테스트"
        }
    )
    assert response.status_code == 404

