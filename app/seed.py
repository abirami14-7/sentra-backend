from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.community import CommunityGroup, CommunityReport
from app.models.route import RouteModel


def seed_community(db: Session) -> None:
    if db.query(CommunityGroup).count() == 0:
        groups = [
            CommunityGroup(
                name="Women Safety Group",
                area="Anna Nagar",
                distance_km=1.2,
                icon_key="people_alt",
                color_hex="#6D28D9",
                member_count=142,
            ),
            CommunityGroup(
                name="Chennai Women Network",
                area="Chennai",
                distance_km=2.5,
                icon_key="female",
                color_hex="#EC4899",
                member_count=380,
            ),
            CommunityGroup(
                name="Safe Streets Initiative",
                area="Chennai",
                distance_km=3.8,
                icon_key="location_city",
                color_hex="#7C3AED",
                member_count=96,
            ),
        ]
        db.add_all(groups)
        db.commit()

    if db.query(CommunityReport).count() == 0:
        now = datetime.utcnow()
        reports = [
            CommunityReport(
                user_id=None,
                reporter_name="Anonymous",
                area="Whitefield",
                incident_type="Harassment",
                description="Verbal harassment near the bus stop around 10 PM.",
                validations=4,
                reported_at=now - timedelta(hours=6),
            ),
            CommunityReport(
                user_id=None,
                reporter_name="Anonymous",
                area="MG Road",
                incident_type="Poor Lighting",
                description="Street lights not working along the metro stretch.",
                validations=7,
                reported_at=now - timedelta(days=1),
            ),
            CommunityReport(
                user_id=None,
                reporter_name="Anonymous",
                area="Indiranagar",
                incident_type="Stalking",
                description="Suspicious following reported twice this week.",
                validations=9,
                reported_at=now - timedelta(days=2),
            ),
            CommunityReport(
                user_id=None,
                reporter_name="Anonymous",
                area="Anna Nagar",
                incident_type="Theft",
                description="Phone snatched near the park entrance.",
                validations=2,
                reported_at=now - timedelta(days=3),
            ),
        ]
        db.add_all(reports)
        db.commit()


def seed_routes(db: Session) -> None:
    if db.query(RouteModel).count() > 0:
        return
    routes = [
        RouteModel(
            route_id="r1",
            name="Route A - Main Road",
            origin="MG Road",
            destination="Whitefield",
            distance_km=14.2,
            duration_min=38,
            risk_score=34,
            risk_level="LOW",
            confidence=88,
            is_safer=True,
        ),
        RouteModel(
            route_id="r2",
            name="Route B - Shortcut",
            origin="MG Road",
            destination="Whitefield",
            distance_km=11.0,
            duration_min=27,
            risk_score=68,
            risk_level="MEDIUM",
            confidence=82,
            is_safer=False,
        ),
        RouteModel(
            route_id="r3",
            name="Route C - Ring Road",
            origin="MG Road",
            destination="Whitefield",
            distance_km=18.5,
            duration_min=44,
            risk_score=22,
            risk_level="LOW",
            confidence=90,
            is_safer=False,
        ),
    ]
    db.add_all(routes)
    db.commit()
