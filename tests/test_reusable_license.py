import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models, security_utils
from app.routers.auth import redeem_license_entry


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_license_key_format_no_confusing_chars():
    forbidden = set("l1iIoO0")
    for _ in range(200):
        key = security_utils.generate_license_key()
        assert len(key) == 9
        assert not (set(key) & forbidden), f"Forbidden char in {key}"
        assert any(c.isdigit() for c in key), f"No digit in {key}"
        assert any(c.isalpha() for c in key), f"No letter in {key}"
        assert key == key.upper()


def test_reusable_license_multiple_users_once_per_user(db_session):
    lic = models.License(
        key="8AH2K9M2J",
        status="ACTIVE",
        duration_days=365,
        is_reusable=True,
        max_uses=None,
        use_count=0,
        label="Cuaderno 2026"
    )
    u1 = models.User(username="u1@test.com", email="u1@test.com", hashed_password="x")
    u2 = models.User(username="u2@test.com", email="u2@test.com", hashed_password="x")
    db_session.add_all([lic, u1, u2])
    db_session.commit()

    # User 1 redeems -> succeeds, +365 days, license stays ACTIVE
    exp1 = redeem_license_entry(db_session, lic, u1, user_id=u1.id)
    db_session.commit()
    assert lic.status == "ACTIVE"
    assert lic.use_count == 1
    assert exp1 > datetime.utcnow() + timedelta(days=364)

    # User 1 tries to redeem again -> blocked
    with pytest.raises(HTTPException) as exc:
        redeem_license_entry(db_session, lic, u1, user_id=u1.id)
    assert exc.value.status_code == 400

    # User 2 redeems same code -> succeeds
    exp2 = redeem_license_entry(db_session, lic, u2, user_id=u2.id)
    db_session.commit()
    assert lic.status == "ACTIVE"
    assert lic.use_count == 2
    assert exp2 > datetime.utcnow() + timedelta(days=364)


def test_reusable_license_subuser_and_max_uses_and_revoke(db_session):
    lic = models.License(
        key="7BG3N8P4Q",
        status="ACTIVE",
        duration_days=365,
        is_reusable=True,
        max_uses=2,
        use_count=0
    )
    teacher = models.User(username="t@test.com", email="t@test.com", hashed_password="x", is_teacher=True)
    db_session.add_all([lic, teacher])
    db_session.commit()

    s1 = models.SubUser(parent_user_id=teacher.id, name="Alumno 1")
    s2 = models.SubUser(parent_user_id=teacher.id, name="Alumno 2")
    s3 = models.SubUser(parent_user_id=teacher.id, name="Alumno 3")
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    # Subuser 1 and 2 succeed
    redeem_license_entry(db_session, lic, s1, subuser_id=s1.id)
    redeem_license_entry(db_session, lic, s2, subuser_id=s2.id)
    db_session.commit()
    assert lic.use_count == 2

    # Subuser 3 hits max_uses=2
    with pytest.raises(HTTPException) as exc_max:
        redeem_license_entry(db_session, lic, s3, subuser_id=s3.id)
    assert exc_max.value.status_code == 403

    # Revoked license blocks redemption even with higher max_uses
    lic.max_uses = 10
    lic.status = "REVOKED"
    db_session.commit()
    with pytest.raises(HTTPException) as exc_rev:
        redeem_license_entry(db_session, lic, s3, subuser_id=s3.id)
    assert exc_rev.value.status_code == 403
