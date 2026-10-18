from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
class Security(BaseModel):
    symbol: str = Field(pattern=r"^[A-Z0-9][A-Z0-9.\-]{0,15}$")
    name: str
    sector: str = "未分类"
    themes: list[str] = []
    kind: str = "CS"
    active: bool = True
    exchange: str = "XNYS"
class Report(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    symbol: str = Field(pattern=r"^[A-Z0-9][A-Z0-9.\-]{0,15}$")
    name: str
    sector: str
    themes: list[str]
    session: str
    next_session: str
    simulated: bool
    close: float = Field(gt=0)
    change_pct: float
    dollar_volume: float = Field(ge=0)
    relative_volume: float = Field(ge=0)
    indicators: dict[str,float]
    support: float
    resistance: float
    outlook: Literal["看涨","震荡","看跌"]
    scenarios: dict[str,str]
    catalysts: list[str]
    risks: list[str]
    sources: list[str]
    missing: list[str]
    score: float
    rank: int
    rank_change: int | None = None
    probability_up: None = None  # No validated probability model is deployed.
    summary: str
