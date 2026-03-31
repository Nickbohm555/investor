from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SignalType = Literal["congress", "insider", "gov_contract", "lobbying"]
SignalDirection = Literal["positive", "negative", "mixed", "neutral"]


class QuiverRowModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class CongressionalTrade(QuiverRowModel):
    ticker: str = Field(alias="Ticker")
    transaction: str = Field(alias="Transaction")
    representative: Optional[str] = Field(default=None, alias="Representative")


class InsiderTrade(QuiverRowModel):
    ticker: str = Field(alias="Ticker")
    transaction: str = Field(alias="Transaction")
    insider_name: Optional[str] = Field(default=None, alias="InsiderName")


class GovernmentContractAward(QuiverRowModel):
    ticker: str = Field(alias="Ticker")
    amount: Optional[str] = Field(default=None, alias="Amount")
    agency: Optional[str] = Field(default=None, alias="Agency")
    amount_description: Optional[str] = Field(default=None, alias="AmountDescription")


class LobbyingDisclosure(QuiverRowModel):
    ticker: str = Field(alias="Ticker")
    client: Optional[str] = Field(default=None, alias="Client")
    issue: Optional[str] = Field(default=None, alias="Issue")


class SignalRecord(BaseModel):
    signal_type: SignalType
    ticker: str
    observed_at: datetime = Field(
        default_factory=lambda: datetime(1970, 1, 1, tzinfo=timezone.utc)
    )
    direction: SignalDirection
    magnitude_note: str
    source_note: str


class TickerEvidenceBundle(BaseModel):
    ticker: str
    supporting_signals: List[SignalRecord] = Field(default_factory=list)
    contradictory_signals: List[SignalRecord] = Field(default_factory=list)
    source_summary: List[str] = Field(default_factory=list)
