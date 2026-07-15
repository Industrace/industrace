from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.models.network_probe import NetworkProbe
from app.services.network_probe_service import NetworkProbeService
from app.services.probe_auth import get_probe_api_key, log_probe_auth_failure
from app.services.rate_limiter import check_probe_rate_limit
from app.services.rbac import require_permission
from app.services.audit_decorator import audit_log_action
from app.config import settings
from app.errors.exceptions import ErrorCodeException
from app.errors.error_codes import ErrorCode
from app.schemas.network_probe import (
    NetworkProbeCreate,
    NetworkProbeUpdate,
    NetworkProbeRead,
    NetworkProbeCreateResponse,
    ProbeHeartbeatCreate,
    ProbeDataTransmissionCreate,
    ProbeStatusResponse,
    ProbeConfigurationResponse,
    ProbeStatisticsResponse,
)


router = APIRouter(prefix="/network-probes", tags=["network-probes"])


def _enforce_probe_rate_limit(api_key: str, rate_limit: str) -> None:
    if not check_probe_rate_limit(api_key, rate_limit):
        raise ErrorCodeException(status_code=429, error_code=ErrorCode.RATE_LIMIT_EXCEEDED)


@router.post("", response_model=NetworkProbeCreateResponse)
@audit_log_action("create", "NetworkProbe", model_class=NetworkProbe)
async def create_network_probe(
    probe_data: NetworkProbeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("network_probes", 3)),
):
    probe = NetworkProbeService.create_probe(db, current_user.tenant_id, probe_data)
    return probe


@router.get("", response_model=List[NetworkProbeRead])
async def get_network_probes(
    site_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("network_probes", 1)),
):
    return NetworkProbeService.get_probes_by_tenant(db, current_user.tenant_id, site_id)


@router.get("/overview")
async def get_probes_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("network_probes", 1)),
):
    return NetworkProbeService.get_tenant_probes_overview(db, current_user.tenant_id)


@router.post("/heartbeat")
async def register_probe_heartbeat(
    heartbeat_data: ProbeHeartbeatCreate,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_probe_api_key),
):
    _enforce_probe_rate_limit(api_key, settings.PROBE_RATE_LIMIT_HEARTBEAT)
    heartbeat = NetworkProbeService.register_heartbeat(db, api_key, heartbeat_data)
    if not heartbeat:
        log_probe_auth_failure("invalid API key on heartbeat", request=request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key non valida")
    return {"message": "Heartbeat registrato", "timestamp": heartbeat.timestamp}


@router.post("/data-transmission")
async def register_probe_data_transmission(
    transmission_data: ProbeDataTransmissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_probe_api_key),
):
    _enforce_probe_rate_limit(api_key, settings.PROBE_RATE_LIMIT_DATA)
    transmission = NetworkProbeService.register_data_transmission(db, api_key, transmission_data)
    if not transmission:
        log_probe_auth_failure("invalid API key on data-transmission", request=request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key non valida")
    processed_devices = transmission_data.discovered_devices or []
    processed_count = len(processed_devices)
    return {
        "message": "Trasmissione registrata",
        "timestamp": transmission.timestamp,
        "status": transmission.status,
        "processed_devices": processed_count,
    }


@router.get("/configuration/{probe_id}", response_model=ProbeConfigurationResponse)
async def get_probe_configuration(
    probe_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_probe_api_key),
):
    _enforce_probe_rate_limit(api_key, settings.PROBE_RATE_LIMIT_CONFIG)
    probe = NetworkProbeService.get_probe_by_api_key(db, api_key)
    if not probe or str(probe.id) != str(probe_id):
        log_probe_auth_failure("API key mismatch for configuration", request=request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key non valida per questa sonda")

    config = {
        "interface_name": probe.interface_name,
        "promiscuous_mode": probe.promiscuous_mode,
        "capture_filter": probe.capture_filter,
        "max_packet_size": probe.max_packet_size,
        "buffer_size": probe.buffer_size,
        "enabled_protocols": probe.enabled_protocols,
        "sampling_rate": probe.sampling_rate,
        "metadata_extraction": probe.metadata_extraction,
        "payload_analysis": probe.payload_analysis,
        "heartbeat_interval": probe.heartbeat_interval,
        "data_transmission_interval": probe.data_transmission_interval,
        "max_retry_attempts": probe.max_retry_attempts,
    }

    return {
        "probe_id": probe.id,
        "configuration": config,
        "last_update": probe.last_config_update or probe.updated_at or probe.created_at,
        "version": probe.software_version or "1.0.0",
    }


@router.get("/{probe_id}", response_model=NetworkProbeRead)
async def get_network_probe(
    probe_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("network_probes", 1)),
):
    probe = NetworkProbeService.get_probe_by_id(db, probe_id, current_user.tenant_id)
    if not probe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sonda non trovata")
    return probe


@router.put("/{probe_id}", response_model=NetworkProbeRead)
@audit_log_action("update", "NetworkProbe", model_class=NetworkProbe)
async def update_network_probe(
    probe_id: UUID,
    update_data: NetworkProbeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("network_probes", 2)),
):
    probe = NetworkProbeService.update_probe(db, probe_id, current_user.tenant_id, update_data)
    if not probe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sonda non trovata")
    return probe


@router.delete("/{probe_id}")
@audit_log_action("delete", "NetworkProbe", model_class=NetworkProbe)
async def delete_network_probe(
    probe_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("network_probes", 3)),
):
    ok = NetworkProbeService.delete_probe(db, probe_id, current_user.tenant_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sonda non trovata")
    return {"message": "Sonda eliminata"}


@router.post("/{probe_id}/deauthorize")
@audit_log_action("deauthorize", "NetworkProbe", model_class=NetworkProbe)
async def deauthorize_network_probe(
    probe_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("network_probes", 3)),
):
    probe = NetworkProbeService.deauthorize_probe(db, probe_id, current_user.tenant_id)
    if not probe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sonda non trovata")

    return {"message": "Sonda de-autorizzata", "probe_id": str(probe.id)}


@router.get("/{probe_id}/status", response_model=ProbeStatusResponse)
async def get_probe_status(
    probe_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("network_probes", 1)),
):
    data = NetworkProbeService.get_probe_status(db, probe_id, current_user.tenant_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sonda non trovata")
    return data


@router.get("/{probe_id}/statistics", response_model=ProbeStatisticsResponse)
async def get_probe_statistics(
    probe_id: UUID,
    time_range: str = Query("7d", pattern=r"^\d+[hd]$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm=Depends(require_permission("network_probes", 1)),
):
    data = NetworkProbeService.get_probe_statistics(
        db,
        probe_id,
        current_user.tenant_id,
        time_range=time_range,
    )
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sonda non trovata")
    return data
