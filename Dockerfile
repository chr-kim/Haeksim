# Multi-stage build로 빌드 도구와 런타임 분리
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Poetry와 export 플러그인 설치
RUN pip install --no-cache-dir poetry>=1.8.0 poetry-plugin-export

# Poetry 설정
RUN poetry config virtualenvs.create false

COPY backend/pyproject.toml backend/poetry.lock ./

# requirements.txt 생성
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# 런타임 이미지
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# 시스템 패키지 최소화 및 정리
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# requirements.txt 복사 및 종속성 설치
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt && \
    rm -rf /root/.cache/pip

# 애플리케이션 코드 복사
COPY backend/. .

# 보안을 위한 사용자 생성
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]