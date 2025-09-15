# backend/api/passage.py

from fastapi import APIRouter, HTTPException, status
from typing import Union
from schemas.passage import (
    PassageGenerateRequest, 
    PassageGenerateResponse,
    PassageOnlyResponse,
    PassageChoicesResponse
)
from services import passage_service

router = APIRouter()

@router.post(
    "/generate", 
    response_model=Union[PassageOnlyResponse, PassageChoicesResponse, PassageGenerateResponse], 
    status_code=status.HTTP_201_CREATED
)
async def generate_passage(request: PassageGenerateRequest):
    result = await passage_service.generate_and_save_passage(request)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="지문 생성에 실패했습니다."
        )
    
    # ✅ features에 따라 적절한 Pydantic 모델로 반환
    if request.features == "지문요약 핵심파악":
        return PassageOnlyResponse(**result)
    elif request.features == "선지 분석 & 논리 평가":
        return PassageChoicesResponse(**result)
    else:
        return PassageGenerateResponse(**result)
