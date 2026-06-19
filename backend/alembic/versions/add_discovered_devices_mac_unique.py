"""Normalize discovered device MACs and add unique constraint per probe

Revision ID: add_discovered_mac_unique
Revises: merge_compliance_notif_heads
Create Date: 2026-05-26

"""

from alembic import op
import sqlalchemy as sa


revision = "add_discovered_mac_unique"
down_revision = "merge_compliance_notif_heads"
branch_labels = None
depends_on = None


def _normalize_mac(mac: str) -> str | None:
    import re

    if not mac:
        return None
    hex_only = re.sub(r"[^0-9A-Fa-f]", "", mac.strip())
    if len(hex_only) != 12:
        return None
    hex_only = hex_only.upper()
    return ":".join(hex_only[i : i + 2] for i in range(0, 12, 2))


def upgrade():
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, tenant_id, probe_id, mac_address, last_seen "
            "FROM discovered_devices ORDER BY last_seen DESC NULLS LAST"
        )
    ).fetchall()

    seen: set[tuple] = set()
    for row in rows:
        device_id, tenant_id, probe_id, mac_address, _last_seen = row
        normalized = _normalize_mac(mac_address)
        if not normalized:
            continue
        key = (str(tenant_id), str(probe_id), normalized)
        if key in seen:
            conn.execute(
                sa.text("DELETE FROM discovered_devices WHERE id = :id"),
                {"id": str(device_id)},
            )
            continue
        seen.add(key)
        if normalized != mac_address:
            conn.execute(
                sa.text("UPDATE discovered_devices SET mac_address = :mac WHERE id = :id"),
                {"mac": normalized, "id": str(device_id)},
            )

    op.create_index(
        "uq_discovered_devices_tenant_probe_mac",
        "discovered_devices",
        ["tenant_id", "probe_id", "mac_address"],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_discovered_devices_tenant_probe_mac", table_name="discovered_devices")
