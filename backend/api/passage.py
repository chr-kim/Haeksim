# backend/api/passage.py
from fastapi import APIRouter, HTTPException, status
from schemas.passage import PassageGenerateRequest, PassageGenerateResponse
from services import passage_service

router = APIRouter()

@router.post("/generate", response_model=PassageGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_passage(request: PassageGenerateRequest):
    result = await passage_service.generate_and_save_passage(request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="지문 생성에 실패했습니다.",
        )
    return result