from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.ml.predictor import get_predictor
from app.models.risk_log import RiskPredictionLog
from app.models.user import User
from app.schemas.risk import RiskContext, RiskPredictionOut

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post("/predict", response_model=RiskPredictionOut)
def predict(
    payload: RiskContext,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    predictor = get_predictor()
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Risk model not loaded. Run the ML pipeline first.",
        )
    result = predictor.predict(payload.model_dump())

    try:
        log = RiskPredictionLog(
            user_id=current.id,
            risk_score=int(result["risk_score"]),
            risk_level=str(result["risk_level"]),
            confidence=int(result["confidence"]),
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()

    return result
