"""Add network probes and discovered devices

Revision ID: add_network_probe_models
Revises: add_tenant_syslog
Create Date: 2026-02-12

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "add_network_probe_models"
down_revision = "add_tenant_syslog"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "network_probes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("probe_type", sa.String(length=50), nullable=False, server_default="network"),
        sa.Column("interface_name", sa.String(length=100), nullable=False),
        sa.Column("interface_ip", sa.String(length=45), nullable=True),
        sa.Column("mirror_port", sa.String(length=100), nullable=True),
        sa.Column("promiscuous_mode", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("capture_filter", sa.String(length=500), nullable=True),
        sa.Column("max_packet_size", sa.Integer(), nullable=False, server_default="1518"),
        sa.Column("buffer_size", sa.Integer(), nullable=False, server_default="65536"),
        sa.Column("enabled_protocols", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sampling_rate", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("metadata_extraction", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("payload_analysis", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="inactive"),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_data_received", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_packets_captured", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_bytes_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_connections", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_devices_seen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("heartbeat_interval", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("data_transmission_interval", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("max_retry_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("api_key", sa.String(length=255), nullable=False),
        sa.Column("encryption_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("ssl_verify", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("location_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("hardware_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("software_version", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_config_update", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_network_probes_tenant_id", "network_probes", ["tenant_id"])
    op.create_index("ix_network_probes_site_id", "network_probes", ["site_id"])
    op.create_index("ix_network_probes_api_key", "network_probes", ["api_key"], unique=True)

    op.create_table(
        "probe_heartbeats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("probe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("cpu_usage", sa.Float(), nullable=True),
        sa.Column("memory_usage", sa.Float(), nullable=True),
        sa.Column("disk_usage", sa.Float(), nullable=True),
        sa.Column("network_throughput", sa.Float(), nullable=True),
        sa.Column("packets_per_second", sa.Float(), nullable=True),
        sa.Column("bytes_per_second", sa.Float(), nullable=True),
        sa.Column("active_connections", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["probe_id"], ["network_probes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_probe_heartbeats_probe_id", "probe_heartbeats", ["probe_id"])
    op.create_index("ix_probe_heartbeats_timestamp", "probe_heartbeats", ["timestamp"])

    op.create_table(
        "probe_data_transmissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("probe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("transmission_type", sa.String(length=50), nullable=False),
        sa.Column("data_size", sa.Integer(), nullable=False),
        sa.Column("compression_ratio", sa.Float(), nullable=True),
        sa.Column("encryption_used", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("new_devices_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_connections_detected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("protocol_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("discovered_devices", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["probe_id"], ["network_probes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_probe_data_transmissions_probe_id", "probe_data_transmissions", ["probe_id"])
    op.create_index("ix_probe_data_transmissions_timestamp", "probe_data_transmissions", ["timestamp"])

    # Se un upgrade fallisce a metà, l'ENUM può restare in DB senza tabelle collegate.
    # Lo rimuoviamo per evitare DuplicateObject quando poi eseguiamo CREATE TABLE.
    op.execute("DROP TYPE IF EXISTS devicediscoverystatus")

    device_status_enum = sa.Enum(
        "discovered",
        "matched",
        "imported",
        "assigned",
        "ignored",
        "conflict",
        name="devicediscoverystatus",
    )

    op.create_table(
        "discovered_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("probe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mac_address", sa.String(length=17), nullable=False),
        sa.Column("ip_addresses", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("vendor", sa.String(length=100), nullable=True),
        sa.Column("device_type", sa.String(length=100), nullable=True),
        sa.Column("protocols", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("firmware_version", sa.String(length=100), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("discovery_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confidence_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", device_status_enum, nullable=False, server_default="discovered"),
        sa.Column("matched_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("match_confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("match_reason", sa.String(length=255), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("auto_import_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["probe_id"], ["network_probes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_asset_id"], ["assets.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_discovered_devices_tenant_id", "discovered_devices", ["tenant_id"])
    op.create_index("ix_discovered_devices_site_id", "discovered_devices", ["site_id"])
    op.create_index("ix_discovered_devices_probe_id", "discovered_devices", ["probe_id"])
    op.create_index("ix_discovered_devices_mac_address", "discovered_devices", ["mac_address"])
    op.create_index("ix_discovered_devices_last_seen", "discovered_devices", ["last_seen"])
    op.create_index("ix_discovered_devices_matched_asset_id", "discovered_devices", ["matched_asset_id"])


def downgrade():
    op.drop_index("ix_discovered_devices_matched_asset_id", table_name="discovered_devices")
    op.drop_index("ix_discovered_devices_last_seen", table_name="discovered_devices")
    op.drop_index("ix_discovered_devices_mac_address", table_name="discovered_devices")
    op.drop_index("ix_discovered_devices_probe_id", table_name="discovered_devices")
    op.drop_index("ix_discovered_devices_site_id", table_name="discovered_devices")
    op.drop_index("ix_discovered_devices_tenant_id", table_name="discovered_devices")
    op.drop_table("discovered_devices")

    device_status_enum = sa.Enum(
        "discovered",
        "matched",
        "imported",
        "assigned",
        "ignored",
        "conflict",
        name="devicediscoverystatus",
    )
    device_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_probe_data_transmissions_timestamp", table_name="probe_data_transmissions")
    op.drop_index("ix_probe_data_transmissions_probe_id", table_name="probe_data_transmissions")
    op.drop_table("probe_data_transmissions")

    op.drop_index("ix_probe_heartbeats_timestamp", table_name="probe_heartbeats")
    op.drop_index("ix_probe_heartbeats_probe_id", table_name="probe_heartbeats")
    op.drop_table("probe_heartbeats")

    op.drop_index("ix_network_probes_api_key", table_name="network_probes")
    op.drop_index("ix_network_probes_site_id", table_name="network_probes")
    op.drop_index("ix_network_probes_tenant_id", table_name="network_probes")
    op.drop_table("network_probes")
