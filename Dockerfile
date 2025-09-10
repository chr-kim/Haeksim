# --- 1단계: 빌더 스테이지 ---
FROM python:3.11-slim-bookworm AS builder
WORKDIR /app
RUN pip install poetry
# ✨ [수정] backend 폴더 안의 poetry 파일들만 복사
COPY backend/poetry.lock backend/pyproject.toml ./
RUN poetry config virtualenvs.in-project true && poetry install --no-dev --no-root

# --- 2단계: 최종 스테이지 ---
FROM python:3.11-slim-bookworm AS final
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
# ✨ [수정] 우리 backend 소스코드 전체를 복사
COPY ./backend .

# 루트리스 설정
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser
ENV PATH="/app/.venv/bin:$PATH"

# 서버 실행 (수정 없음)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
