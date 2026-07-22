import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.network_probe import NetworkProbe, ProbeHeartbeat, ProbeDataTransmission
from app.models.discovered_device import DiscoveredDevice, DeviceDiscoveryStatus
from app.schemas.network_probe import (
    NetworkProbeCreate,
    NetworkProbeUpdate,
    ProbeHeartbeatCreate,
    ProbeDataTransmissionCreate,
)
from app.services.oui_lookup import lookup_vendor_by_mac
from app.services.mac_utils import normalize_mac_address
from app.config import settings


class NetworkProbeService:
    @staticmethod
    def refresh_stale_probe_statuses(
        db: Session,
        tenant_id: Optional[uuid.UUID] = None,
        stale_seconds: Optional[int] = None,
    ) -> int:
        """Mark probes without recent heartbeat as inactive."""
        threshold = stale_seconds or settings.PROBE_HEARTBEAT_STALE_SECONDS
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=threshold)
        query = db.query(NetworkProbe).filter(NetworkProbe.status == "active")
        if tenant_id:
            query = query.filter(NetworkProbe.tenant_id == tenant_id)

        updated = 0
        for probe in query.all():
            last_hb = probe.last_heartbeat
            if last_hb is not None and last_hb.tzinfo is None:
                last_hb = last_hb.replace(tzinfo=timezone.utc)
            if last_hb is None or last_hb < cutoff:
                probe.status = "inactive"
                updated += 1
        if updated:
            db.commit()
        return updated

    @staticmethod
    def purge_old_probe_telemetry(
        db: Session,
        retention_days: Optional[int] = None,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, int]:
        """Delete heartbeat and transmission records older than retention policy."""
        days = retention_days or settings.PROBE_RETENTION_DAYS
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        hb_query = db.query(ProbeHeartbeat).filter(ProbeHeartbeat.timestamp < cutoff)
        tx_query = db.query(ProbeDataTransmission).filter(ProbeDataTransmission.timestamp < cutoff)
        if tenant_id:
            hb_query = hb_query.join(NetworkProbe).filter(NetworkProbe.tenant_id == tenant_id)
            tx_query = tx_query.join(NetworkProbe).filter(NetworkProbe.tenant_id == tenant_id)

        deleted_heartbeats = hb_query.delete(synchronize_session=False)
        deleted_transmissions = tx_query.delete(synchronize_session=False)
        if deleted_heartbeats or deleted_transmissions:
            db.commit()
        return {
            "deleted_heartbeats": int(deleted_heartbeats or 0),
            "deleted_transmissions": int(deleted_transmissions or 0),
        }

    @staticmethod
    def generate_api_key() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_probe(db: Session, tenant_id: uuid.UUID, probe_data: NetworkProbeCreate) -> NetworkProbe:
        api_key = NetworkProbeService.generate_api_key()
        probe = NetworkProbe(
            tenant_id=tenant_id,
            api_key=api_key,
            status="inactive",
            **probe_data.model_dump(),
        )
        db.add(probe)
        db.commit()
        db.refresh(probe)
        return probe

    @staticmethod
    def get_probe_by_id(db: Session, probe_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[NetworkProbe]:
        return (
            db.query(NetworkProbe)
            .filter(and_(NetworkProbe.id == probe_id, NetworkProbe.tenant_id == tenant_id))
            .first()
        )

    @staticmethod
    def get_probe_by_api_key(db: Session, api_key: str) -> Optional[NetworkProbe]:
        return db.query(NetworkProbe).filter(NetworkProbe.api_key == api_key).first()

    @staticmethod
    def get_probes_by_tenant(
        db: Session, tenant_id: uuid.UUID, site_id: Optional[uuid.UUID] = None
    ) -> List[NetworkProbe]:
        NetworkProbeService.refresh_stale_probe_statuses(db, tenant_id=tenant_id)
        query = db.query(NetworkProbe).filter(NetworkProbe.tenant_id == tenant_id)
        if site_id:
            query = query.filter(NetworkProbe.site_id == site_id)
        return query.order_by(NetworkProbe.name).all()

    @staticmethod
    def update_probe(
        db: Session, probe_id: uuid.UUID, tenant_id: uuid.UUID, update_data: NetworkProbeUpdate
    ) -> Optional[NetworkProbe]:
        probe = NetworkProbeService.get_probe_by_id(db, probe_id, tenant_id)
        if not probe:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(probe, field, value)

        probe.last_config_update = datetime.now(timezone.utc)
        db.commit()
        db.refresh(probe)
        return probe

    @staticmethod
    def delete_probe(db: Session, probe_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        exists = (
            db.query(NetworkProbe.id)
            .filter(and_(NetworkProbe.id == probe_id, NetworkProbe.tenant_id == tenant_id))
            .first()
        )
        if not exists:
            return False

        # Bulk delete: evita db.delete(probe) che farebbe UPDATE probe_id=NULL sui figli in sessione.
        db.query(ProbeHeartbeat).filter(ProbeHeartbeat.probe_id == probe_id).delete(
            synchronize_session=False
        )
        db.query(ProbeDataTransmission).filter(
            ProbeDataTransmission.probe_id == probe_id
        ).delete(synchronize_session=False)
        db.query(DiscoveredDevice).filter(DiscoveredDevice.probe_id == probe_id).delete(
            synchronize_session=False
        )
        deleted = (
            db.query(NetworkProbe)
            .filter(and_(NetworkProbe.id == probe_id, NetworkProbe.tenant_id == tenant_id))
            .delete(synchronize_session=False)
        )
        if not deleted:
            return False

        # Bulk delete non rimuove oggetti dalla sessione: senza expunge, al commit
        # l'ORM tenterebbe UPDATE probe_id=NULL sui discovered_devices ancora tracciati.
        db.flush()
        db.expunge_all()
        db.commit()
        return True

    @staticmethod
    def deauthorize_probe(db: Session, probe_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[NetworkProbe]:
        """
        De-autorizza una sonda invalidando la API key corrente.
        La sonda in esecuzione non riuscira' piu' ad autenticarsi con la key precedente.
        """
        probe = NetworkProbeService.get_probe_by_id(db, probe_id, tenant_id)
        if not probe:
            return None

        probe.api_key = NetworkProbeService.generate_api_key()
        probe.status = "inactive"
        probe.last_config_update = datetime.now(timezone.utc)

        db.commit()
        db.refresh(probe)
        return probe

    @staticmethod
    def register_heartbeat(
        db: Session, api_key: str, heartbeat_data: ProbeHeartbeatCreate
    ) -> Optional[ProbeHeartbeat]:
        probe = NetworkProbeService.get_probe_by_api_key(db, api_key)
        if not probe:
            return None

        payload = heartbeat_data.model_dump()
        payload.pop("probe_id", None)

        heartbeat = ProbeHeartbeat(probe_id=probe.id, **payload)
        db.add(heartbeat)

        probe.last_heartbeat = datetime.now(timezone.utc)
        probe.status = "active"

        # Best-effort stats update (approx)
        if heartbeat_data.packets_per_second is not None:
            probe.total_packets_captured += int(heartbeat_data.packets_per_second * probe.heartbeat_interval)
        if heartbeat_data.bytes_per_second is not None:
            probe.total_bytes_processed += int(heartbeat_data.bytes_per_second * probe.heartbeat_interval)
        if heartbeat_data.active_connections is not None:
            probe.active_connections = heartbeat_data.active_connections

        db.commit()
        db.refresh(heartbeat)
        return heartbeat

    @staticmethod
    def register_data_transmission(
        db: Session, api_key: str, transmission_data: ProbeDataTransmissionCreate
    ) -> Optional[ProbeDataTransmission]:
        probe = NetworkProbeService.get_probe_by_api_key(db, api_key)
        if not probe:
            return None

        payload = transmission_data.model_dump()
        payload.pop("probe_id", None)

        transmission = ProbeDataTransmission(probe_id=probe.id, **payload)
        db.add(transmission)

        probe.last_data_received = datetime.now(timezone.utc)
        probe.status = "active"

        processed_devices = 0
        if transmission_data.discovered_devices:
            processed_devices = NetworkProbeService.upsert_discovered_devices(
                db=db,
                probe=probe,
                devices=transmission_data.discovered_devices,
            )

        db.commit()
        db.refresh(transmission)
        transmission.status = transmission.status or "success"
        return transmission

    @staticmethod
    def upsert_discovered_devices(
        db: Session,
        probe: NetworkProbe,
        devices: List[Dict[str, Any]],
        max_devices: int = 1000,
    ) -> int:
        """
        Upsert dei dispositivi scoperti per una singola trasmissione.
        Chiave logica: (tenant_id, probe_id, mac_address).
        """
        processed = 0
        now = datetime.now(timezone.utc)

        def _ensure_aware_utc(dt: datetime) -> datetime:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        for device_data in (devices or [])[:max_devices]:
            mac = normalize_mac_address(device_data.get("mac_address"))
            if not mac:
                continue

            # Timestamps: preferisci quelli del device, fallback a now
            first_seen = now
            last_seen = now
            first_seen_raw = device_data.get("first_seen")
            last_seen_raw = device_data.get("last_seen")
            try:
                if first_seen_raw:
                    first_seen = datetime.fromisoformat(first_seen_raw.replace("Z", "+00:00"))
            except Exception:
                first_seen = now
            try:
                if last_seen_raw:
                    last_seen = datetime.fromisoformat(last_seen_raw.replace("Z", "+00:00"))
            except Exception:
                last_seen = now

            ip_addresses = device_data.get("ip_addresses") or []
            protocols = device_data.get("protocols") or []
            resolved_vendor = lookup_vendor_by_mac(mac, default=(device_data.get("vendor") or "Unknown Vendor"))

            existing = (
                db.query(DiscoveredDevice)
                .filter(
                    and_(
                        DiscoveredDevice.tenant_id == probe.tenant_id,
                        DiscoveredDevice.probe_id == probe.id,
                        DiscoveredDevice.mac_address == mac,
                    )
                )
                .first()
            )

            if existing:
                existing_last_seen = _ensure_aware_utc(existing.last_seen) if existing.last_seen else None
                incoming_last_seen = _ensure_aware_utc(last_seen)
                existing.last_seen = max(existing_last_seen, incoming_last_seen) if existing_last_seen else incoming_last_seen
                existing.discovery_count = (existing.discovery_count or 0) + 1
                existing.ip_addresses = sorted(list(set((existing.ip_addresses or []) + list(ip_addresses))))
                existing.protocols = sorted(list(set((existing.protocols or []) + list(protocols))))
                existing.hostname = device_data.get("hostname") or existing.hostname
                existing.vendor = resolved_vendor or existing.vendor
                existing.device_type = device_data.get("device_type") or existing.device_type
                existing.firmware_version = device_data.get("firmware_version") or existing.firmware_version
                existing.raw_data = {**(existing.raw_data or {}), **device_data}
                processed += 1
                continue

            created = DiscoveredDevice(
                tenant_id=probe.tenant_id,
                site_id=probe.site_id,
                probe_id=probe.id,
                mac_address=mac,
                ip_addresses=list(ip_addresses),
                hostname=device_data.get("hostname"),
                vendor=resolved_vendor,
                device_type=device_data.get("device_type"),
                protocols=list(protocols),
                firmware_version=device_data.get("firmware_version"),
                first_seen=first_seen,
                last_seen=last_seen,
                discovery_count=1,
                confidence_score=0,
                status=DeviceDiscoveryStatus.DISCOVERED.value,
                raw_data=device_data,
                auto_import_enabled=False,
            )
            db.add(created)
            probe.unique_devices_seen = (probe.unique_devices_seen or 0) + 1
            processed += 1

        return processed

    @staticmethod
    def get_probe_status(db: Session, probe_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        NetworkProbeService.refresh_stale_probe_statuses(db, tenant_id=tenant_id)
        probe = NetworkProbeService.get_probe_by_id(db, probe_id, tenant_id)
        if not probe:
            return None

        recent_heartbeat = (
            db.query(ProbeHeartbeat)
            .filter(ProbeHeartbeat.probe_id == probe_id)
            .order_by(desc(ProbeHeartbeat.timestamp))
            .first()
        )

        current_metrics = {}
        if recent_heartbeat:
            current_metrics = {
                "cpu_usage": recent_heartbeat.cpu_usage,
                "memory_usage": recent_heartbeat.memory_usage,
                "disk_usage": recent_heartbeat.disk_usage,
                "packets_per_second": recent_heartbeat.packets_per_second,
                "bytes_per_second": recent_heartbeat.bytes_per_second,
                "active_connections": recent_heartbeat.active_connections,
            }

        return {
            "probe_id": probe.id,
            "name": probe.name,
            "status": probe.status,
            "last_heartbeat": probe.last_heartbeat,
            "last_data_received": probe.last_data_received,
            "uptime_seconds": None,
            "health_score": NetworkProbeService._calculate_health_score(probe),
            "current_metrics": current_metrics,
        }

    @staticmethod
    def _calculate_health_score(probe: NetworkProbe) -> float:
        score = 100.0
        if probe.last_heartbeat:
            delta = datetime.now(timezone.utc) - probe.last_heartbeat
            if delta > timedelta(minutes=5):
                score -= 30
            elif delta > timedelta(minutes=2):
                score -= 15
        if probe.status == "error":
            score -= 50
        elif probe.status == "maintenance":
            score -= 20
        return max(0.0, score)

    @staticmethod
    def _parse_probe_time_range(time_range: str) -> timedelta:
        normalized = (time_range or "7d").strip().lower()
        if normalized.endswith("h"):
            return timedelta(hours=max(1, int(normalized[:-1])))
        if normalized.endswith("d"):
            return timedelta(days=max(1, int(normalized[:-1])))
        return timedelta(days=7)

    @staticmethod
    def get_probe_statistics(
        db: Session,
        probe_id: uuid.UUID,
        tenant_id: uuid.UUID,
        time_range: str = "7d",
    ) -> Optional[Dict[str, Any]]:
        probe = NetworkProbeService.get_probe_by_id(db, probe_id, tenant_id)
        if not probe:
            return None

        window = NetworkProbeService._parse_probe_time_range(time_range)
        cutoff = datetime.now(timezone.utc) - window

        heartbeats = (
            db.query(ProbeHeartbeat)
            .filter(ProbeHeartbeat.probe_id == probe_id, ProbeHeartbeat.timestamp >= cutoff)
            .order_by(desc(ProbeHeartbeat.timestamp))
            .all()
        )
        transmissions = (
            db.query(ProbeDataTransmission)
            .filter(ProbeDataTransmission.probe_id == probe_id, ProbeDataTransmission.timestamp >= cutoff)
            .order_by(desc(ProbeDataTransmission.timestamp))
            .all()
        )

        protocol_distribution: Dict[str, int] = {}
        for tx in transmissions:
            breakdown = tx.protocol_breakdown or {}
            for proto, count in breakdown.items():
                if isinstance(count, (int, float)):
                    protocol_distribution[str(proto)] = protocol_distribution.get(str(proto), 0) + int(count)

        if not protocol_distribution:
            devices = (
                db.query(DiscoveredDevice)
                .filter(DiscoveredDevice.probe_id == probe_id, DiscoveredDevice.tenant_id == tenant_id)
                .all()
            )
            for device in devices:
                for proto in device.protocols or []:
                    protocol_distribution[str(proto)] = protocol_distribution.get(str(proto), 0) + 1

        traffic_volume: Dict[str, float] = {}
        heartbeat_interval = probe.heartbeat_interval or 30
        for hb in heartbeats:
            if hb.bytes_per_second is None or not hb.timestamp:
                continue
            day_key = hb.timestamp.date().isoformat()
            traffic_volume[day_key] = traffic_volume.get(day_key, 0.0) + float(hb.bytes_per_second * heartbeat_interval)

        def _avg(values: List[Optional[float]]) -> float:
            nums = [float(v) for v in values if v is not None]
            return sum(nums) / len(nums) if nums else 0.0

        performance_metrics = {
            "cpu_usage_avg": round(_avg([hb.cpu_usage for hb in heartbeats]), 2),
            "memory_usage_avg": round(_avg([hb.memory_usage for hb in heartbeats]), 2),
            "disk_usage_avg": round(_avg([hb.disk_usage for hb in heartbeats]), 2),
            "packets_per_second_avg": round(_avg([hb.packets_per_second for hb in heartbeats]), 2),
            "bytes_per_second_avg": round(_avg([hb.bytes_per_second for hb in heartbeats]), 2),
            "heartbeat_count": float(len(heartbeats)),
            "transmission_count": float(len(transmissions)),
        }

        if heartbeats:
            errors = sum(hb.error_count or 0 for hb in heartbeats)
            error_rate = errors / len(heartbeats)
        elif transmissions:
            failed = len([tx for tx in transmissions if tx.status == "failed"])
            error_rate = failed / len(transmissions)
        else:
            error_rate = 0.0

        return {
            "probe_id": probe.id,
            "time_range": time_range,
            "total_packets": int(probe.total_packets_captured or 0),
            "total_bytes": int(probe.total_bytes_processed or 0),
            "unique_devices": int(probe.unique_devices_seen or 0),
            "active_connections": int(probe.active_connections or 0),
            "protocol_distribution": protocol_distribution,
            "traffic_volume": traffic_volume,
            "error_rate": round(error_rate, 4),
            "performance_metrics": performance_metrics,
        }

    @staticmethod
    def get_tenant_probes_overview(db: Session, tenant_id: uuid.UUID) -> Dict[str, Any]:
        probes = NetworkProbeService.get_probes_by_tenant(db, tenant_id)

        total_probes = len(probes)
        active_probes = len([p for p in probes if p.status == "active"])
        error_probes = len([p for p in probes if p.status == "error"])
        maintenance_probes = len([p for p in probes if p.status == "maintenance"])

        # Lightweight aggregates: count transmissions by tenant via join
        total_transmissions = (
            db.query(func.count(ProbeDataTransmission.id))
            .join(NetworkProbe, NetworkProbe.id == ProbeDataTransmission.probe_id)
            .filter(NetworkProbe.tenant_id == tenant_id)
            .scalar()
            or 0
        )

        return {
            "total_probes": total_probes,
            "active_probes": active_probes,
            "error_probes": error_probes,
            "maintenance_probes": maintenance_probes,
            "health_percentage": (active_probes / total_probes * 100) if total_probes else 0,
            "total_transmissions": int(total_transmissions),
        }
