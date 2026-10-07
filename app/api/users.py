from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import EmergencyContact, User
from app.schemas.user import (
    EmergencyContactCreate,
    EmergencyContactOut,
    UserWithContacts,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserWithContacts)
def read_me(current: User = Depends(get_current_user)):
    return current


@router.get("/me/emergency-contacts", response_model=List[EmergencyContactOut])
def list_contacts(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == current.id)
        .order_by(EmergencyContact.priority.asc(), EmergencyContact.id.asc())
        .all()
    )


@router.post(
    "/me/emergency-contacts",
    response_model=EmergencyContactOut,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(
    payload: EmergencyContactCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = EmergencyContact(user_id=current.id, **payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete(
    "/me/emergency-contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_contact(
    contact_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.get(EmergencyContact, contact_id)
    if not contact or contact.user_id != current.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )
    db.delete(contact)
    db.commit()
    return None
