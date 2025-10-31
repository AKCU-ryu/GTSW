# app/routers/reco.py
from fastapi import APIRouter
from typing import List
from app.services.ml.reco_simple import recommend_topn

router = APIRouter()

@router.get("/topn")
def topn(codes: List[str] = ["005930.KS","000660.KS","035720.KS"], n: int = 3):
    """입력 종목 리스트 중 상위 n개 추천"""
    out = recommend_topn(codes, n=n)
    return {"reco": out}
