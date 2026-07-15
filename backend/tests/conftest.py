"""Pytest fixtures for backend integration tests (SQLite in-memory by default)."""
import os
import uuid

import pytest
from sqlalchemy import JSON, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import SecurityRequirement, SecurityZone, Tenant, Site
from app.models.requirement_enhancement import RequirementEnhancement
from app.models.sr_assessment import SRAssessment
from app.models.network_probe import NetworkProbe, ProbeHeartbeat, ProbeDataTransmission
from app.models.discovered_device import DiscoveredDevice
from app.models.asset import Asset
from app.models.asset_interface import AssetInterface
from app.models.asset_type import AssetType
from app.models.asset_status import AssetStatus


def _sqlite_jsonb_compat(tables, url: str) -> None:
    if not url.startswith("sqlite"):
        return
    for table in tables:
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()


@pytest.fixture(scope="function")
def db_session():
    url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    tables = [
        Tenant.__table__,
        Site.__table__,
        SecurityZone.__table__,
        SecurityRequirement.__table__,
        RequirementEnhancement.__table__,
        SRAssessment.__table__,
        NetworkProbe.__table__,
        ProbeHeartbeat.__table__,
        ProbeDataTransmission.__table__,
        DiscoveredDevice.__table__,
        AssetType.__table__,
        AssetStatus.__table__,
        Asset.__table__,
        AssetInterface.__table__,
    ]
    _sqlite_jsonb_compat(tables, url)
    Base.metadata.create_all(bind=engine, tables=tables)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=tables)


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid.uuid4(), name="Test Tenant", slug=f"test-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    db_session.commit()
    return t


@pytest.fixture
def zone(db_session, tenant):
    z = SecurityZone(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Test Zone",
        security_level_target=2,
        compliance_status="not_assessed",
    )
    db_session.add(z)
    db_session.commit()
    db_session.refresh(z)
    return z


@pytest.fixture
def sr_min_sl_1(db_session):
    sr = SecurityRequirement(
        id=uuid.uuid4(),
        requirement_id="SR 9.9",
        requirement_category="SR",
        title="Integration test SR",
        applies_to_zones=True,
        applies_to_conduits=False,
        applies_to_assets=False,
        min_security_level=1,
        max_security_level=4,
        standard_version="62443-3-3:2013",
    )
    db_session.add(sr)
    for level in range(1, 5):
        db_session.add(
            RequirementEnhancement(
                id=uuid.uuid4(),
                security_requirement_id=sr.id,
                enhancement_level=level,
                title=f"SR 9.9 — RE {level}",
                description=f"RE {level} text",
            )
        )
    db_session.commit()
    db_session.refresh(sr)
    return sr


@pytest.fixture
def site(db_session, tenant):
    s = Site(id=uuid.uuid4(), tenant_id=tenant.id, name="Test Site", code="TS1")
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s
