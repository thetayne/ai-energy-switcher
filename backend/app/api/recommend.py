from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

class UserInfo(BaseModel):
    location: str
    provider: str
    cost: str
    preferences: str

class Provider(BaseModel):
    name: str
    price: str
    reason: str

router = APIRouter()

@router.post("/recommend", response_model=List[Provider])
async def recommend(user: UserInfo):
    # Dummy recommendations
    recs = [
        Provider(name="E.ON", price="€85/mo", reason="Lowest price for your area"),
        Provider(name="Vattenfall", price="€89/mo", reason="Best green energy option"),
        Provider(name="EnBW", price="€92/mo", reason="Top rated for customer service"),
    ]
    return recs 