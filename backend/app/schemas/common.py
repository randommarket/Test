from datetime import date, datetime
from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    sector: str | None = None


class CompanyOut(BaseModel):
    id: int
    name: str
    sector: str | None

    class Config:
        from_attributes = True


class ActualIn(BaseModel):
    period: date
    category: str
    amount: float


class ScenarioCreate(BaseModel):
    name: str
    revenue_growth: float
    gross_margin: float
    opex_growth: float


class ScenarioOut(ScenarioCreate):
    id: int

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "analyst"


class UserOut(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True


class OrgSettingsUpdate(BaseModel):
    runway_risk_threshold: float
    revenue_drop_threshold: float
    margin_drop_threshold: float


class OrgSettingsOut(OrgSettingsUpdate):
    id: int

    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    id: int
    org_id: int
    user_id: int | None
    action: str
    detail: str | None
    created_at: datetime

    class Config:
        from_attributes = True
