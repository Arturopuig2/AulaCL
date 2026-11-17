import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models, security_utils
from app.routers.auth import (
    redeem_license_entry,
    delete_unused_license,
    toggle_license_status,
    toggle_redemption_status,
)


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


def test_delete_unused_and_revoke_used_single_license(db_session):
    admin = models.User(username="admin", email="admin@test.com", hashed_password="x")
    unused_lic = models.License(key="UNUSED234", status="ACTIVE", duration_days=365, is_reusable=False)
    used_lic = models.License(key="USED23456", status="ACTIVE", duration_days=365, is_reusable=False)
    student = models.User(username="s@test.com", email="s@test.com", hashed_password="x")
    db_session.add_all([admin, unused_lic, used_lic, student])
    db_session.commit()

    # Delete unused succeeds
    res_del = delete_unused_license(unused_lic.id, current_user=admin, db=db_session)
    assert res_del["deleted"] is True
    assert db_session.query(models.License).filter(models.License.key == "UNUSED234").first() is None

    # Redeem used_lic
    exp = redeem_license_entry(db_session, used_lic, student, user_id=student.id)
    db_session.commit()
    assert student.access_expires_at == exp

    # Cannot delete a used license
    with pytest.raises(HTTPException) as exc_del:
        delete_unused_license(used_lic.id, current_user=admin, db=db_session)
    assert exc_del.value.status_code == 400

    # Revoke removes student's access, status becomes REVOKED
    toggle_license_status(used_lic.id, current_user=admin, db=db_session)
    db_session.refresh(student)
    db_session.refresh(used_lic)
    assert used_lic.status == "REVOKED"
    assert student.access_expires_at is None

    # Reactivate restores student's access, status becomes USED
    toggle_license_status(used_lic.id, current_user=admin, db=db_session)
    db_session.refresh(student)
    db_session.refresh(used_lic)
    assert used_lic.status == "USED"
    assert student.access_expires_at == exp


def test_revoke_and_reactivate_reusable_redemption(db_session):
    admin = models.User(username="admin", email="admin@test.com", hashed_password="x")
    lic = models.License(key="REUS23456", status="ACTIVE", duration_days=365, is_reusable=True)
    u1 = models.User(username="u1@test.com", email="u1@test.com", hashed_password="x")
    db_session.add_all([admin, lic, u1])
    db_session.commit()

    exp = redeem_license_entry(db_session, lic, u1, user_id=u1.id)
    db_session.commit()
    red = db_session.query(models.LicenseRedemption).filter(models.LicenseRedemption.license_id == lic.id).first()
    assert red is not None
    assert u1.access_expires_at == exp

    # Revoke redemption -> withdraws u1's access
    toggle_redemption_status(red.id, current_user=admin, db=db_session)
    db_session.refresh(u1)
    db_session.refresh(red)
    assert red.is_revoked is True
    assert u1.access_expires_at is None

    # Reactivate redemption -> restores u1's access
    toggle_redemption_status(red.id, current_user=admin, db=db_session)
    db_session.refresh(u1)
    db_session.refresh(red)
    assert red.is_revoked is False
    assert u1.access_expires_at == exp
