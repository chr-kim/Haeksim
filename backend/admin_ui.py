# admin_ui.py
import streamlit as st
import requests
import json

st.title("✍️ 문제 풀이 평가 시스템 (테스트 페이지)")

# 입력 폼 생성
problem_id = st.number_input("문제 ID", value=1)
user_answer_id = st.selectbox("선택 답안", [1, 2, 3, 4, 5])
user_reasoning = st.text_area("답안 선택 근거를 입력하세요", height=200)

if st.button("평가 요청하기"):
    with st.spinner("Gemini API가 평가 중입니다..."):
        try:
            # FastAPI 서버로 요청 전송
            response = requests.post(
                "http://localhost:8000/evaluate",
                json={
                    "problem_id": problem_id,
                    "user_answer_id": user_answer_id,
                    "user_reasoning": user_reasoning,
                }
            )
            response.raise_for_status() # 오류 발생 시 예외 처리

            st.success("평가 완료!")
            st.json(response.json()) # 결과를 JSON 형태로 예쁘게 출력

        except requests.exceptions.RequestException as e:
            st.error(f"API 요청 실패: {e}")
        except json.JSONDecodeError:
            st.error("응답을 JSON으로 파싱할 수 없습니다.")
