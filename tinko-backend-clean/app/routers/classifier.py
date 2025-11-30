from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from ..services.classifier import classify_event


class ClassifyIn(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None


class ClassifyOut(BaseModel):
    ok: bool
    data: Dict[str, Any]


router = APIRouter(tags=["classifier"])


@router.post("/classify", response_model=ClassifyOut)
def classify(body: ClassifyIn) -> ClassifyOut:
    result = classify_event(body.code, body.message)
    return ClassifyOut(ok=True, data=result)
