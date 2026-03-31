from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BrokerMode(str, Enum):
    paper = "paper"
    live = "live"


class BrokerPolicySnapshot(BaseModel):
    broker_mode: BrokerMode
    account_buying_power: str
    asset_tradable: bool
    asset_fractionable: bool
    order_shape: dict[str, str]


class OrderProposal(BaseModel):
    run_id: str
    recommendation_id: int
    broker_mode: BrokerMode
    symbol: str
    side: str
    order_type: str
    time_in_force: str
    qty: Optional[str] = None
    notional: Optional[str] = None
    client_order_id: str


class BrokerArtifact(BaseModel):
    id: int
    run_id: str
    recommendation_id: int
    broker_mode: BrokerMode
    symbol: str
    side: str
    order_type: str
    time_in_force: str
    qty: Optional[str] = None
    notional: Optional[str] = None
    client_order_id: str
    status: str = Field(default="draft_ready")
    policy_snapshot_json: dict
