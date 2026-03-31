from __future__ import annotations

from decimal import Decimal

from app.schemas.broker import BrokerMode, BrokerPolicySnapshot, OrderProposal


class BrokerPolicyError(ValueError):
    """Raised when a broker proposal violates deterministic v1 policy."""


def validate_order_proposal(
    proposal: OrderProposal,
    *,
    account: dict,
    asset: dict,
    broker_mode: str,
    base_url: str,
) -> BrokerPolicySnapshot:
    if broker_mode not in {"paper", "live"}:
        raise BrokerPolicyError("Unsupported broker mode")
    if broker_mode == "paper" and base_url != "https://paper-api.alpaca.markets":
        raise BrokerPolicyError("paper mode requires https://paper-api.alpaca.markets")
    if broker_mode == "live" and base_url != "https://api.alpaca.markets":
        raise BrokerPolicyError("live mode requires https://api.alpaca.markets")
    if proposal.side != "buy":
        raise BrokerPolicyError("Only buy proposals are supported")
    if proposal.order_type != "market":
        raise BrokerPolicyError("Only market orders are supported")
    if proposal.time_in_force != "day":
        raise BrokerPolicyError("Only day orders are supported")
    if account.get("trading_blocked"):
        raise BrokerPolicyError("Account is trading blocked")
    if asset.get("tradable") is not True:
        raise BrokerPolicyError("Asset is not tradable")
    if proposal.notional is not None and asset.get("fractionable") is not True:
        raise BrokerPolicyError("Notional orders require a fractionable asset")

    buying_power = Decimal(str(account["buying_power"]))
    estimated_cost = Decimal(proposal.notional or proposal.qty or "0")
    if buying_power < estimated_cost:
        raise BrokerPolicyError("Insufficient buying power")

    return BrokerPolicySnapshot(
        broker_mode=BrokerMode(broker_mode),
        account_buying_power=str(account["buying_power"]),
        asset_tradable=bool(asset.get("tradable")),
        asset_fractionable=bool(asset.get("fractionable")),
        order_shape={
            "side": proposal.side,
            "order_type": proposal.order_type,
            "time_in_force": proposal.time_in_force,
        },
    )
