from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.community import (
    CommunityGroup,
    CommunityReport,
    GroupMembership,
)
from app.models.user import User
from app.schemas.community import (
    GroupCreate,
    GroupOut,
    ReportCreate,
    ReportOut,
)

router = APIRouter(prefix="/community", tags=["community"])


def _membership_ids(db: Session, user_id: int) -> set:
    rows = (
        db.query(GroupMembership.group_id)
        .filter(GroupMembership.user_id == user_id)
        .all()
    )
    return {r[0] for r in rows}


@router.get("/groups", response_model=List[GroupOut])
def list_groups(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = (
        db.query(CommunityGroup)
        .order_by(CommunityGroup.distance_km.asc())
        .all()
    )
    joined = _membership_ids(db, current.id)
    out = []
    for g in groups:
        item = GroupOut.model_validate(g)
        item.joined = g.id in joined
        out.append(item)
    return out


@router.post(
    "/groups",
    response_model=GroupOut,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    payload: GroupCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = CommunityGroup(
        name=payload.name,
        area=payload.area,
        distance_km=payload.distance_km,
        icon_key=payload.icon_key or "people_alt",
        color_hex=payload.color_hex or "#6D28D9",
        member_count=1,
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    db.add(GroupMembership(user_id=current.id, group_id=group.id))
    db.commit()

    item = GroupOut.model_validate(group)
    item.joined = True
    return item


@router.post("/groups/{group_id}/join", response_model=GroupOut)
def join_group(
    group_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = db.get(CommunityGroup, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    existing = (
        db.query(GroupMembership)
        .filter(
            GroupMembership.user_id == current.id,
            GroupMembership.group_id == group.id,
        )
        .first()
    )
    if existing is None:
        db.add(GroupMembership(user_id=current.id, group_id=group.id))
        group.member_count += 1
        db.commit()
        db.refresh(group)

    item = GroupOut.model_validate(group)
    item.joined = True
    return item


@router.post("/groups/{group_id}/leave", response_model=GroupOut)
def leave_group(
    group_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = db.get(CommunityGroup, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    existing = (
        db.query(GroupMembership)
        .filter(
            GroupMembership.user_id == current.id,
            GroupMembership.group_id == group.id,
        )
        .first()
    )
    if existing is not None:
        db.delete(existing)
        group.member_count = max(0, group.member_count - 1)
        db.commit()
        db.refresh(group)

    item = GroupOut.model_validate(group)
    item.joined = False
    return item


@router.get("/reports", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_db), limit: int = 50):
    return (
        db.query(CommunityReport)
        .order_by(desc(CommunityReport.reported_at))
        .limit(limit)
        .all()
    )


@router.post(
    "/reports",
    response_model=ReportOut,
    status_code=status.HTTP_201_CREATED,
)
def create_report(
    payload: ReportCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = CommunityReport(
        user_id=current.id,
        reporter_name=payload.reporter_name or current.name,
        area=payload.area,
        incident_type=payload.incident_type,
        description=payload.description,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.post("/reports/{report_id}/validate", response_model=ReportOut)
def validate_report(
    report_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.get(CommunityReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    report.validations += 1
    db.commit()
    db.refresh(report)
    return report
