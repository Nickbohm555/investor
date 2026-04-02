from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SignalType = Literal["congress", "insider", "gov_contract", "lobbying", "bill"]
SignalDirection = Literal["positive", "negative", "mixed", "neutral"]


class QuiverRowModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class CongressionalTrade(QuiverRowModel):
    ticker: str = Field(alias="Ticker")
    transaction: str = Field(alias="Transaction")
    representative: Optional[str] = Field(default=None, alias="Representative")
    filed: Optional[str] = Field(default=None, alias="Filed")
    traded: Optional[str] = Field(default=None, alias="Traded")
    trade_size_usd: Optional[str] = Field(default=None, alias="Trade_Size_USD")
    party: Optional[str] = Field(default=None, alias="Party")
    chamber: Optional[str] = Field(default=None, alias="Chamber")


class InsiderTrade(QuiverRowModel):
    ticker: str = Field(alias="Ticker")
    transaction: str = Field(alias="Transaction")
    insider_name: Optional[str] = Field(default=None, alias="InsiderName")
    date: Optional[str] = Field(default=None, alias="Date")
    file_date: Optional[str] = Field(default=None, alias="fileDate")
    shares: Optional[str] = Field(default=None, alias="Shares")
    price_per_share: Optional[str] = Field(default=None, alias="PricePerShare")


class GovernmentContractAward(QuiverRowModel):
    ticker: str = Field(alias="Ticker")
    amount: Optional[str] = Field(default=None, alias="Amount")
    agency: Optional[str] = Field(default=None, alias="Agency")
    amount_description: Optional[str] = Field(default=None, alias="AmountDescription")


class LobbyingDisclosure(QuiverRowModel):
    ticker: str = Field(alias="Ticker")
    client: Optional[str] = Field(default=None, alias="Client")
    issue: Optional[str] = Field(default=None, alias="Issue")
    date: Optional[str] = Field(default=None, alias="Date")
    amount: Optional[str] = Field(default=None, alias="Amount")
    specific_issue: Optional[str] = Field(default=None, alias="Specific_Issue")
    registrant: Optional[str] = Field(default=None, alias="Registrant")


class BillSummary(QuiverRowModel):
    title: str = Field(alias="Title")
    congress: Optional[str] = Field(default=None, alias="Congress")
    number: Optional[str] = Field(default=None, alias="Number")
    origin_chamber: Optional[str] = Field(default=None, alias="originChamber")
    current_chamber: Optional[str] = Field(default=None, alias="currentChamber")
    bill_type: Optional[str] = Field(default=None, alias="billType")
    summary: Optional[str] = Field(default=None, alias="Summary")
    url: Optional[str] = Field(default=None, alias="URL")
    last_action: Optional[str] = Field(default=None, alias="lastAction")
    last_action_date: Optional[str] = Field(default=None, alias="lastActionDate")


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
    freshness_summary: str = ""
    conflict_summary: str = ""
    latest_signal_at: Optional[datetime] = None
