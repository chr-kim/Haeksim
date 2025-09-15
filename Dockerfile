# Multi-stage build로 빌드 도구와 런타임 분리
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Poetry와 export 플러그인 설치
RUN pip install --no-cache-dir poetry>=1.8.0 poetry-plugin-export

# Poetry 설정
RUN poetry config virtualenvs.create false

# pyproject.toml만 복사 (poetry.lock은 자동 생성)
COPY backend/pyproject.toml ./

# lock 파일 자동 생성 (파일이 없으면 새로 생성됨)
RUN poetry lock

# requirements.txt 생성 (개발 종속성 제외)
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --without dev

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

# CUDA 방지 및 캐시 최적화
RUN pip install --no-cache-dir \
    --index-url https://pypi.org/simple \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt && \
    rm requirements.txt && \
    rm -rf /root/.cache/pip

# 보안을 위한 사용자/그룹 생성 (먼저 실행)
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# 데이터 디렉토리 생성 및 권한 설정 (사용자 생성 후)
RUN mkdir -p data && \
    chown -R appuser:appgroup data

# 애플리케이션 코드 복사
COPY backend/. .

# 전체 앱 디렉토리 권한 설정 (코드 복사 후)
RUN chown -R appuser:appgroup /app

# 사용자 전환 (모든 설정 완료 후)
USER appuser

EXPOSE 8000

# 프로덕션 최적화된 uvicorn 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--loop", "asyncio"]
