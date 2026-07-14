import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.sso_oauth_state import SsoOAuthState
from app.services import sso_state_store as store


def test_db_sso_state_roundtrip(monkeypatch):
    monkeypatch.setattr(store, "_get_redis", lambda: None)

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine, tables=[SsoOAuthState.__table__])
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        tenant_id = uuid.uuid4()
        store.store_sso_state("state-1", "verifier", tenant_id, db)
        payload = store.consume_sso_state("state-1", db)
        assert payload is not None
        assert payload["code_verifier"] == "verifier"
        assert payload["tenant_id"] == str(tenant_id)
        assert store.consume_sso_state("state-1", db) is None
    finally:
        db.close()


def test_memory_sso_state_is_single_use(monkeypatch):
    monkeypatch.setattr(store, "_get_redis", lambda: None)
    tenant_id = uuid.uuid4()
    store.store_sso_state("state-2", "verifier-2", tenant_id, db=None)
    payload = store.consume_sso_state("state-2", db=None)
    assert payload is not None
    assert store.consume_sso_state("state-2", db=None) is None
