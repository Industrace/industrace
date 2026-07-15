from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, or_, false
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.asset_interface import AssetInterface
from app.models.discovered_device import DiscoveredDevice
from app.schemas.discovered_device import DiscoveredDeviceMatchCandidate


MatchMaps = Tuple[Dict[str, List[Tuple[AssetInterface, Asset]]], Dict[str, List[Tuple[AssetInterface, Asset]]]]


class DiscoveredDeviceService:
    @staticmethod
    def build_candidate_maps(
        db: Session,
        tenant_id: uuid.UUID,
        macs: set[str],
        ips: set[str],
    ) -> MatchMaps:
        candidate_interfaces_query = (
            db.query(AssetInterface, Asset)
            .join(
                Asset,
                and_(Asset.id == AssetInterface.asset_id, Asset.deleted_at.is_(None)),
            )
            .filter(Asset.tenant_id == tenant_id, AssetInterface.tenant_id == tenant_id)
        )
        if macs or ips:
            candidate_interfaces_query = candidate_interfaces_query.filter(
                or_(
                    AssetInterface.mac_address.in_(list(macs)) if macs else false(),
                    AssetInterface.ip_address.in_(list(ips)) if ips else false(),
                )
            )

        mac_matches: Dict[str, List[Tuple[AssetInterface, Asset]]] = {}
        ip_matches: Dict[str, List[Tuple[AssetInterface, Asset]]] = {}
        for iface, asset in candidate_interfaces_query.all():
            if iface.mac_address:
                mac_key = iface.mac_address.lower()
                mac_matches.setdefault(mac_key, []).append((iface, asset))
            if iface.ip_address:
                ip_matches.setdefault(iface.ip_address, []).append((iface, asset))
        return mac_matches, ip_matches

    @staticmethod
    def build_match_candidates(
        device: DiscoveredDevice,
        mac_matches: Dict[str, List[Tuple[AssetInterface, Asset]]],
        ip_matches: Dict[str, List[Tuple[AssetInterface, Asset]]],
    ) -> List[DiscoveredDeviceMatchCandidate]:
        unique_possible: List[DiscoveredDeviceMatchCandidate] = []
        seen: set[tuple] = set()

        if device.mac_address:
            for iface, asset in mac_matches.get(device.mac_address.lower(), []):
                key = (str(asset.id), "mac", None, iface.mac_address)
                if key in seen:
                    continue
                seen.add(key)
                unique_possible.append(
                    DiscoveredDeviceMatchCandidate(
                        asset_id=asset.id,
                        asset_name=asset.name,
                        match_type="mac",
                        matched_mac=iface.mac_address,
                        matched_ip=None,
                    )
                )

        for ip in device.ip_addresses or []:
            for iface, asset in ip_matches.get(ip, []):
                key = (str(asset.id), "ip", ip, iface.mac_address)
                if key in seen:
                    continue
                seen.add(key)
                unique_possible.append(
                    DiscoveredDeviceMatchCandidate(
                        asset_id=asset.id,
                        asset_name=asset.name,
                        match_type="ip",
                        matched_mac=None,
                        matched_ip=ip,
                    )
                )

        return unique_possible

    @staticmethod
    def select_best_match(
        candidates: List[DiscoveredDeviceMatchCandidate],
    ) -> Optional[DiscoveredDeviceMatchCandidate]:
        for candidate in candidates:
            if candidate.match_type == "mac":
                return candidate
        return candidates[0] if candidates else None

    @staticmethod
    def find_matches_for_device(
        db: Session,
        tenant_id: uuid.UUID,
        device_id: uuid.UUID,
    ) -> Optional[Dict[str, object]]:
        device = (
            db.query(DiscoveredDevice)
            .filter(and_(DiscoveredDevice.id == device_id, DiscoveredDevice.tenant_id == tenant_id))
            .first()
        )
        if not device:
            return None

        macs = {device.mac_address} if device.mac_address else set()
        ips = {ip for ip in (device.ip_addresses or []) if ip}
        mac_matches, ip_matches = DiscoveredDeviceService.build_candidate_maps(db, tenant_id, macs, ips)
        candidates = DiscoveredDeviceService.build_match_candidates(device, mac_matches, ip_matches)
        best_match = DiscoveredDeviceService.select_best_match(candidates)

        return {
            "device_id": device.id,
            "possible_matches": candidates,
            "best_match_asset_id": best_match.asset_id if best_match else None,
            "best_match_asset_name": best_match.asset_name if best_match else None,
            "best_match_type": best_match.match_type if best_match else None,
        }
