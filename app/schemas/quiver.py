from __future__ import annotations

from typing import Literal, Optional

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


class LobbyingDisclosure(QuiverRowModel):
    ticker: str = Field(alias="Ticker")
    client: Optional[str] = Field(default=None, alias="Client")
    issue: Optional[str] = Field(default=None, alias="Issue")
