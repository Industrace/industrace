"""Tests for CompositeRiskScoringEngine and RiskPropagationService."""
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.risk_propagation import RiskPropagationService
from app.services.risk_scoring import CompositeRiskScoringEngine


def _asset(**kwargs):
    defaults = {
        "remote_access": False,
        "remote_access_type": None,
        "physical_access_ease": None,
        "purdue_level": None,
        "connections": [],
        "business_criticality": None,
        "tenant_id": None,
        "id": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestCompositeRiskScoringEngine:
    def setup_method(self):
        self.engine = CompositeRiskScoringEngine()

    def test_missing_business_criticality_returns_null_final_score(self):
        asset = _asset(remote_access=True)
        result = self.engine.calculate(asset)

        assert result["final_score"] is None
        assert "business_criticality" in result["missing_data"]

    def test_remote_access_and_medium_criticality(self):
        asset = _asset(remote_access=True, business_criticality="medium")
        result = self.engine.calculate(asset)

        assert result["final_score"] == 4.3
        assert result["vulnerability"]["score"] == 3
        assert result["impact"]["score"] == 5

    def test_final_score_clamped_to_ten(self):
        asset = _asset(
            remote_access=True,
            remote_access_type="unattended",
            physical_access_ease="unrestricted",
            business_criticality="critical",
            purdue_level=0,
        )
        result = self.engine.calculate(asset)

        assert result["final_score"] <= 10.0
        assert result["final_score"] == 9.3

    def test_low_risk_asset(self):
        asset = _asset(business_criticality="low")
        result = self.engine.calculate(asset)

        assert result["final_score"] == 1.65
        assert result["impact"]["score"] == 2


class TestRiskPropagationService:
    @patch("app.services.risk_propagation.risk_cache")
    @patch("app.services.risk_propagation.get_asset_dependencies_as_dependent")
    def test_dependency_risk_adjustment_direct_dependency(
        self, mock_get_deps, mock_cache
    ):
        mock_cache.get_cached_risk.return_value = None

        tenant_id = uuid.uuid4()
        asset_id = uuid.uuid4()
        dep_asset_id = uuid.uuid4()

        dependency = SimpleNamespace(
            dependency_asset_id=dep_asset_id,
            criticality="critical",
            dependency_type="control_flow",
            confidence="high",
        )
        mock_get_deps.return_value = [dependency]

        dep_asset = SimpleNamespace(risk_score=8.0)
        asset = SimpleNamespace(risk_score=5.0)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            dep_asset,
            asset,
        ]

        adjustment = RiskPropagationService.get_dependency_risk_adjustment(
            db, asset_id, tenant_id, use_cache=False
        )

        # 8 * 1.0 * 0.9 * 1.0 = 7.2, capped at 50% of source (4.0)
        # max_allowed = 10 - 5 = 5 -> result 4.0
        assert adjustment == 4.0

    @patch("app.services.risk_propagation.risk_cache")
    @patch("app.services.risk_propagation.get_asset_dependencies_as_dependent")
    def test_no_dependencies_returns_zero(self, mock_get_deps, mock_cache):
        mock_cache.get_cached_risk.return_value = None
        mock_get_deps.return_value = []

        adjustment = RiskPropagationService.get_dependency_risk_adjustment(
            MagicMock(), uuid.uuid4(), uuid.uuid4(), use_cache=False
        )

        assert adjustment == 0.0
