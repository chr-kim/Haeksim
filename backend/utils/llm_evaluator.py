# utils/llm_evaluator.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)

# JSON 출력을 위한 설정
generation_config = {
  "response_mime_type": "application/json",
}

# 사용할 모델 선택
model = genai.GenerativeModel(
  "gemini-1.5-flash-latest", # 빠르고 저렴한 최신 모델
  generation_config=generation_config
)

async def get_gemini_evaluation(prompt: str) -> dict:
    # 비동기 처리가 필요하다면 genai.GenerativeModel(...).generate_content_async 사용
    response = await model.generate_content_async(prompt)
    return response.text # API가 바로 JSON 텍스트를 반환
