"""Minimal tests for Print System (ReportLab PDF generate + kit options)."""
import uuid
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import JSON, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Tenant, Role, User, Site
from app.models.asset import Asset
from app.models.asset_type import AssetType
from app.models.asset_status import AssetStatus
from app.models.asset_photo import AssetPhoto
from app.models.asset_document import AssetDocument
from app.models.asset_interface import AssetInterface
from app.models.asset_connection import AssetConnection
from app.models.contact import Contact
from app.models.supplier import Supplier
from app.models.manufacturer import Manufacturer
from app.models.location import Location
from app.models.area import Area
from app.models.security_zone import SecurityZone
from app.models.print_template import PrintTemplate
from app.models.print_history import PrintHistory
from app.routers import print as print_router
from app.schemas.print import PrintedKitRequest
from app.services.auth import get_current_user
from app.services.pdf_generator import PDFGenerator
from app.services.rbac_permissions import ADMIN_DEFAULT_PERMISSIONS


def _sqlite_jsonb_compat(tables):
    for table in tables:
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()


@pytest.fixture
def tmp_upload_dir(tmp_path):
    return tmp_path / "prints"


@pytest.fixture
def pdf_gen(tmp_upload_dir):
    return PDFGenerator(upload_dir=str(tmp_upload_dir))


def test_generate_asset_pdf_creates_file(pdf_gen, tmp_upload_dir):
    asset = {
        "id": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "name": "PLC-01 & R&D <unit>",
        "tag": "TAG-1",
        "description": "Test PLC",
        "serial_number": "SN-1",
        "model": "S7-1500",
        "firmware_version": "1.0",
        "custom_fields": {"line": "A&B"},
        "risk_score": 4.5,
        "business_criticality": "high",
        "protocols": ["modbus", "s7"],
        "asset_type": {"name": "PLC"},
        "status": {"name": "Active"},
        "site": {"name": "Plant A"},
        "manufacturer": {"name": "Siemens"},
        "contacts": [],
        "suppliers": [],
        "interfaces": [],
        "connections": [],
        "photos": [],
        "documents": [],
    }
    template = {"key": "asset-card", "name": "Asset Card", "options": {}}
    path = pdf_gen.generate_asset_pdf(
        asset=asset,
        template=template,
        options={"includeQR": True, "language": "en"},
        language="en",
    )
    assert Path(path).is_file()
    assert Path(path).stat().st_size > 100
    with open(path, "rb") as f:
        assert f.read(4) == b"%PDF"


def test_generate_asset_pdf_respects_summary_options(pdf_gen, tmp_upload_dir):
    asset = {
        "id": str(uuid.uuid4()),
        "name": "HMI",
        "custom_fields": {"secret": "x"},
        "risk_score": 8,
        "connections": [
            {
                "target_asset": {"name": "PLC"},
                "connection_type": "ethernet",
                "protocol": "tcp",
            }
        ],
        "asset_type": {"name": "HMI"},
        "status": {"name": "Active"},
        "contacts": [],
        "suppliers": [],
        "interfaces": [],
    }
    path = pdf_gen.generate_asset_pdf(
        asset=asset,
        template={
            "key": "asset-summary",
            "options": {
                "includeQR": False,
                "includeConnections": False,
                "includeRiskMatrix": False,
                "includeCustomFields": False,
            },
        },
        options={},
        language="it",
    )
    assert Path(path).is_file()
    with open(path, "rb") as f:
        assert f.read(4) == b"%PDF"


def test_generate_printed_kit_respects_options(pdf_gen, tmp_upload_dir):
    tenant_id = uuid.uuid4()
    tenant = SimpleNamespace(
        id=tenant_id,
        name="Acme OT",
        slug="acme-ot",
        created_at=datetime.utcnow(),
        is_active=True,
    )
    site = SimpleNamespace(
        name="Plant",
        code="P1",
        address="Via Roma 1",
        description="Main",
    )
    contact = SimpleNamespace(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        phone1="+390000",
        type="admin",
        notes="",
    )
    supplier = SimpleNamespace(
        name="Vendor Co",
        email="v@example.com",
        phone="+39111",
        address="Via Test 1",
        city="Milano",
        description="Critical vendor",
    )
    asset = SimpleNamespace(
        name="HMI-1",
        risk_score=8.0,
        business_criticality="critical",
        tag="H1",
        serial_number="X",
        asset_type=SimpleNamespace(name="HMI"),
        site=SimpleNamespace(name="Plant"),
        location=None,
        manufacturer=SimpleNamespace(name="Vendor"),
        status=SimpleNamespace(name="Active"),
        interfaces=[],
        notes=None,
        description=None,
    )

    full_path = pdf_gen.generate_printed_kit(
        {
            "tenant": tenant,
            "generated_at": datetime.utcnow(),
            "generated_by": "tester",
            "sites": [site],
            "assets": [asset],
            "contacts": [contact],
            "suppliers": [supplier],
        },
        {
            "include_assets": True,
            "include_sites": True,
            "include_contacts": True,
            "include_suppliers": True,
            "language": "en",
        },
    )
    assert Path(full_path).is_file()
    assert str(tenant_id) in full_path
    assert Path(full_path).name.startswith("printed-kit-")

    minimal_path = pdf_gen.generate_printed_kit(
        {
            "tenant": tenant,
            "generated_at": datetime.utcnow(),
            "generated_by": "tester",
        },
        {
            "include_assets": False,
            "include_sites": False,
            "include_contacts": False,
            "include_suppliers": False,
            "language": "it",
        },
    )
    assert Path(minimal_path).is_file()
    assert Path(minimal_path).stat().st_size > 100


def test_printed_kit_request_accepts_camel_and_snake():
    snake = PrintedKitRequest(
        include_assets=False,
        include_sites=True,
        include_contacts=False,
        include_suppliers=True,
        language="it",
    )
    assert snake.include_assets is False
    assert snake.include_sites is True
    assert snake.language == "it"

    camel = PrintedKitRequest.model_validate(
        {
            "includeAssets": False,
            "includeSites": False,
            "includeContacts": True,
            "includeSuppliers": False,
            "lang": "en",
        }
    )
    assert camel.include_contacts is True
    assert camel.include_assets is False
    assert camel.language == "en"


@pytest.fixture
def print_api(tmp_path, monkeypatch):
    upload = tmp_path / "prints"
    upload.mkdir()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        Tenant.__table__,
        Role.__table__,
        User.__table__,
        Site.__table__,
        AssetType.__table__,
        AssetStatus.__table__,
        Manufacturer.__table__,
        Area.__table__,
        Location.__table__,
        SecurityZone.__table__,
        Asset.__table__,
        AssetPhoto.__table__,
        AssetDocument.__table__,
        AssetInterface.__table__,
        AssetConnection.__table__,
        Contact.__table__,
        Supplier.__table__,
        PrintTemplate.__table__,
        PrintHistory.__table__,
        Asset.metadata.tables["asset_contacts"],
        Asset.metadata.tables["asset_suppliers"],
    ]
    _sqlite_jsonb_compat(tables)
    Base.metadata.create_all(bind=engine, tables=tables)
    Session = sessionmaker(bind=engine)
    session = Session()

    tenant_id = uuid.uuid4()
    role_id = uuid.uuid4()
    user_id = uuid.uuid4()
    site_id = uuid.uuid4()
    type_id = uuid.uuid4()
    status_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Print Tenant", slug=f"print-{tenant_id.hex[:8]}")
    role = Role(
        id=role_id,
        tenant_id=tenant_id,
        name="admin",
        permissions=ADMIN_DEFAULT_PERMISSIONS,
    )
    user = User(
        id=user_id,
        tenant_id=tenant_id,
        email=f"print-{user_id.hex[:8]}@test.com",
        password_hash="hash",
        name="Print User",
        role_id=role_id,
        is_active=True,
    )
    site = Site(id=site_id, tenant_id=tenant_id, name="Site A", code="SA")
    asset_type = AssetType(id=type_id, tenant_id=tenant_id, name="PLC")
    status = AssetStatus(id=status_id, tenant_id=tenant_id, name="Active")
    asset = Asset(
        id=asset_id,
        tenant_id=tenant_id,
        site_id=site_id,
        asset_type_id=type_id,
        status_id=status_id,
        name="Asset Print",
        tag="AP-1",
    )
    template = PrintTemplate(
        key="asset-card",
        name="Asset Card",
        component="reportlab-asset-card",
        options={"includeQR": True},
    )
    session.add_all([tenant, role, user, site, asset_type, status, asset, template])
    session.commit()
    session.refresh(user)
    session.refresh(template)
    session.refresh(asset)

    gen = PDFGenerator(upload_dir=str(upload))
    monkeypatch.setattr(print_router, "pdf_generator", gen)

    app = FastAPI()
    app.include_router(print_router.router)

    def override_db():
        yield session

    def override_user():
        return user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    client = TestClient(app)

    try:
        yield {
            "client": client,
            "session": session,
            "user": user,
            "tenant": tenant,
            "asset": asset,
            "template": template,
            "upload": upload,
        }
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=tables)


def test_api_generate_and_download_asset(print_api):
    client = print_api["client"]
    asset = print_api["asset"]
    template = print_api["template"]

    resp = client.post(
        "/print/generate",
        json={
            "asset_id": str(asset.id),
            "template_id": template.id,
            "options": {"language": "en", "includeQR": True},
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["print_id"]
    assert body["file_size"] > 0

    dl = client.get(f"/print/download/{body['print_id']}")
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("application/pdf")
    assert dl.content[:4] == b"%PDF"


def test_api_generate_and_download_kit_with_options(print_api):
    client = print_api["client"]
    tenant = print_api["tenant"]

    resp = client.post(
        "/print/kit",
        json={
            "includeAssets": True,
            "includeSites": True,
            "includeContacts": False,
            "includeSuppliers": False,
            "lang": "it",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["file_url"].startswith("/print/kit/download/")
    assert body["file_size"] > 0

    filename = body["file_url"].rsplit("/", 1)[-1]
    assert filename.startswith("printed-kit-")

    # File must live under tenant directory
    tenant_file = print_api["upload"] / str(tenant.id) / filename
    assert tenant_file.is_file()

    dl = client.get(f"/print/kit/download/{filename}")
    assert dl.status_code == 200
    assert dl.content[:4] == b"%PDF"

    # Reject filenames that are not printed-kit PDFs
    denied = client.get("/print/kit/download/not-a-kit.pdf")
    assert denied.status_code == 403

    missing = client.get("/print/kit/download/printed-kit-does-not-exist.pdf")
    assert missing.status_code == 404


def test_api_generate_by_template_key_and_null_options(print_api):
    client = print_api["client"]
    asset = print_api["asset"]

    resp = client.post(
        "/print/generate",
        json={
            "asset_id": str(asset.id),
            "template_id": "asset-card",
            "options": None,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["print_id"]


def test_api_generate_skips_deleted_asset(print_api):
    client = print_api["client"]
    session = print_api["session"]
    asset = print_api["asset"]
    template = print_api["template"]

    asset.deleted_at = datetime.utcnow()
    session.commit()

    resp = client.post(
        "/print/generate",
        json={
            "asset_id": str(asset.id),
            "template_id": template.id,
            "options": {"language": "en"},
        },
    )
    assert resp.status_code == 404

    asset.deleted_at = None
    session.commit()


def test_api_history_is_tenant_scoped(print_api):
    client = print_api["client"]
    session = print_api["session"]
    user = print_api["user"]
    asset = print_api["asset"]
    template = print_api["template"]

    other_tenant_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    other_role_id = uuid.uuid4()
    other_site_id = uuid.uuid4()
    other_type_id = uuid.uuid4()
    other_status_id = uuid.uuid4()
    other_asset_id = uuid.uuid4()

    other_tenant = Tenant(
        id=other_tenant_id, name="Other", slug=f"other-{other_tenant_id.hex[:8]}"
    )
    other_role = Role(
        id=other_role_id,
        tenant_id=other_tenant_id,
        name="admin",
        permissions=ADMIN_DEFAULT_PERMISSIONS,
    )
    other_user = User(
        id=other_user_id,
        tenant_id=other_tenant_id,
        email=f"other-{other_user_id.hex[:8]}@test.com",
        password_hash="hash",
        name="Other User",
        role_id=other_role_id,
        is_active=True,
    )
    other_site = Site(
        id=other_site_id, tenant_id=other_tenant_id, name="Other Site", code="OS"
    )
    other_type = AssetType(id=other_type_id, tenant_id=other_tenant_id, name="PLC")
    other_status = AssetStatus(
        id=other_status_id, tenant_id=other_tenant_id, name="Active"
    )
    other_asset = Asset(
        id=other_asset_id,
        tenant_id=other_tenant_id,
        site_id=other_site_id,
        asset_type_id=other_type_id,
        status_id=other_status_id,
        name="Other Asset",
        tag="OA-1",
    )
    session.add_all(
        [
            other_tenant,
            other_role,
            other_user,
            other_site,
            other_type,
            other_status,
            other_asset,
        ]
    )
    session.commit()

    mine = PrintHistory(
        asset_id=asset.id,
        template_id=template.id,
        generated_by=user.id,
        status="completed",
    )
    theirs = PrintHistory(
        asset_id=other_asset_id,
        template_id=template.id,
        generated_by=other_user_id,
        status="completed",
    )
    session.add_all([mine, theirs])
    session.commit()

    resp = client.get("/print/history")
    assert resp.status_code == 200, resp.text
    ids = {row["asset_id"] for row in resp.json()}
    assert str(asset.id) in ids
    assert str(other_asset_id) not in ids


def test_template_key_unique_per_tenant(print_api):
    session = print_api["session"]
    tenant_a = print_api["tenant"]
    tenant_b_id = uuid.uuid4()
    tenant_b = Tenant(
        id=tenant_b_id, name="Tenant B", slug=f"tb-{tenant_b_id.hex[:8]}"
    )
    session.add(tenant_b)
    session.commit()

    t1 = PrintTemplate(
        key="shared-card",
        name="A",
        tenant_id=tenant_a.id,
        component="reportlab-asset-card",
    )
    t2 = PrintTemplate(
        key="shared-card",
        name="B",
        tenant_id=tenant_b_id,
        component="reportlab-asset-card",
    )
    session.add_all([t1, t2])
    session.commit()
    assert t1.id != t2.id


def test_api_init_defaults_and_global_template_is_immutable(print_api):
    client = print_api["client"]
    template = print_api["template"]

    denied = client.delete(f"/print/templates/{template.id}")
    assert denied.status_code == 404

    resp = client.post("/print/templates/init-defaults")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["templates"]) == 2

    again = client.post("/print/templates/init-defaults")
    assert again.status_code == 400


def test_printed_kit_request_normalizes_language():
    req = PrintedKitRequest.model_validate({"lang": "it-IT"})
    assert req.language == "it"
