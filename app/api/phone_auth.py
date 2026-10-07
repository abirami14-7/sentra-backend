import random
import secrets
from datetime import datetime, timedelta
from typing import Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security.hashing import hash_password
from app.security.jwt import create_access_token

router = APIRouter(prefix="/auth/phone", tags=["auth"])

# In-memory OTP store: { phone: (code, expires_at) }
_otp_store: Dict[str, Tuple[str, datetime]] = {}

OTP_TTL_SECONDS = 300


class PhoneRequest(BaseModel):
    phone: str = Field(..., min_length=5, max_length=32)


class PhoneRequestResponse(BaseModel):
    phone: str
    demo_code: str
    expires_in: int


class PhoneVerify(BaseModel):
    phone: str = Field(..., min_length=5, max_length=32)
    code: str = Field(..., min_length=4, max_length=8)


class PhoneVerifyResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool


def _normalize_phone(raw: str) -> str:
    return "".join(c for c in raw if c.isdigit() or c == "+")


@router.post("/request", response_model=PhoneRequestResponse)
def request_otp(payload: PhoneRequest):
    phone = _normalize_phone(payload.phone)
    if len(phone) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid phone number.",
        )
    code = f"{random.randint(0, 999999):06d}"
    expires = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    _otp_store[phone] = (code, expires)
    print(f"[SENTRA OTP] {phone} -> {code}", flush=True)
    return PhoneRequestResponse(
        phone=phone,
        demo_code=code,
        expires_in=OTP_TTL_SECONDS,
    )


@router.post("/verify", response_model=PhoneVerifyResponse)
def verify_otp(payload: PhoneVerify, db: Session = Depends(get_db)):
    phone = _normalize_phone(payload.phone)
    entry = _otp_store.get(phone)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP was requested for this number.",
        )
    code, expires = entry
    if datetime.utcnow() > expires:
        _otp_store.pop(phone, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired. Request a new one.",
        )
    if payload.code.strip() != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect OTP.",
        )

    _otp_store.pop(phone, None)

    user = db.scalar(select(User).where(User.phone == phone))
    is_new = user is None

    if is_new:
        synthetic_email = f"phone{phone.lstrip('+')}@sentra.app"
        existing = db.scalar(select(User).where(User.email == synthetic_email))
        if existing is not None:
            user = existing
            is_new = False
        else:
            user = User(
                email=synthetic_email,
                name="SENTRA User",
                phone=phone,
                password_hash=hash_password(secrets.token_urlsafe(24)),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return PhoneVerifyResponse(access_token=token, is_new_user=is_new)
