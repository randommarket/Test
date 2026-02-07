from datetime import date
import csv
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from jose import jwt

from app.auth.security import create_token, hash_password, verify_password
from app.core.config import settings
from app.db.session import get_db
from app.excel.exporter import build_workbook
from app.models.entities import (
    Actual,
    AuditLog,
    Company,
    Mapping,
    Organization,
    OrganizationSetting,
    Scenario,
    Upload,
    User,
)
from app.schemas.common import (
    AuditLogOut,
    CompanyCreate,
    CompanyOut,
    OrgSettingsOut,
    OrgSettingsUpdate,
    ScenarioCreate,
    ScenarioOut,
    UserCreate,
    UserOut,
)
from app.services.finance import CANONICAL_CATEGORIES, ActualRecord, compute_kpis, forecast, sensitivity_grid

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _log(db: Session, org_id: int, user_id: int | None, action: str, detail: str | None = None) -> None:
    db.add(AuditLog(org_id=org_id, user_id=user_id, action=action, detail=detail))
    db.commit()


def _current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token subject")
    user = db.query(User).get(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _require_roles(allowed_roles: list[str]):
    def _role_dependency(user: User = Depends(_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _role_dependency


def _org_setting(db: Session, org_id: int) -> OrganizationSetting:
    settings_row = db.query(OrganizationSetting).filter(OrganizationSetting.org_id == org_id).first()
    if settings_row:
        return settings_row
    settings_row = OrganizationSetting(
        org_id=org_id,
        runway_risk_threshold=settings.runway_risk_threshold,
        revenue_drop_threshold=settings.revenue_drop_threshold,
        margin_drop_threshold=settings.margin_drop_threshold,
    )
    db.add(settings_row)
    db.commit()
    db.refresh(settings_row)
    return settings_row


@router.post("/auth/register")
def register(org_name: str, email: str, password: str, db: Session = Depends(get_db)):
    org = Organization(name=org_name)
    db.add(org)
    db.commit()
    db.refresh(org)
    user = User(org_id=org.id, email=email, hashed_password=hash_password(password), role="org_admin")
    db.add(user)
    db.commit()
    _log(db, org.id, user.id, "user_registered", email)
    return {"org_id": org.id, "user_id": user.id}


@router.post("/auth/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = create_token(str(user.id), settings.access_token_expire_minutes)
    refresh = create_token(str(user.id), settings.refresh_token_expire_minutes)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


@router.get("/users", response_model=list[UserOut])
def list_users(user: User = Depends(_require_roles(["org_admin"])), db: Session = Depends(get_db)):
    return db.query(User).filter(User.org_id == user.org_id).all()


@router.post("/users", response_model=UserOut)
def create_user(
    payload: UserCreate,
    user: User = Depends(_require_roles(["org_admin"])),
    db: Session = Depends(get_db),
):
    new_user = User(
        org_id=user.org_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    _log(db, user.org_id, user.id, "user_created", payload.email)
    return new_user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user_role(
    user_id: int,
    role: str,
    user: User = Depends(_require_roles(["org_admin"])),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id, User.org_id == user.org_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.role = role
    db.commit()
    _log(db, user.org_id, user.id, "user_role_updated", f"{target.email}:{role}")
    return target


@router.post("/companies", response_model=CompanyOut)
def create_company(
    payload: CompanyCreate,
    user: User = Depends(_require_roles(["org_admin", "analyst"])),
    db: Session = Depends(get_db),
):
    company = Company(org_id=user.org_id, name=payload.name, sector=payload.sector)
    db.add(company)
    db.commit()
    db.refresh(company)
    _log(db, user.org_id, user.id, "company_created", company.name)
    return company


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(user: User = Depends(_current_user), db: Session = Depends(get_db)):
    return db.query(Company).filter(Company.org_id == user.org_id).all()


@router.post("/companies/{company_id}/actuals")
def upload_actuals(
    company_id: int,
    file: UploadFile = File(...),
    user: User = Depends(_require_roles(["org_admin", "analyst"])),
    db: Session = Depends(get_db),
):
    content = file.file.read().decode("utf-8")
    df = pd.read_csv(StringIO(content))
    if not {"period", "category", "amount"}.issubset(df.columns):
        raise HTTPException(status_code=400, detail="CSV must include period, category, amount")
    db.add(Upload(company_id=company_id, filename=file.filename, raw_text=content))
    mappings = {
        m.source_account: m.canonical_category
        for m in db.query(Mapping).filter(Mapping.company_id == company_id).all()
    }
    for _, row in df.iterrows():
        source_category = str(row["category"])
        category = source_category
        if category not in CANONICAL_CATEGORIES:
            category = mappings.get(source_category)
            if category is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Category '{source_category}' missing mapping to canonical schema.",
                )
        actual = Actual(
            company_id=company_id,
            period=date.fromisoformat(str(row["period"])),
            category=category,
            amount=float(row["amount"]),
        )
        db.add(actual)
    db.commit()
    _log(db, user.org_id, user.id, "actuals_uploaded", file.filename)
    return {"status": "ok"}


@router.get("/companies/{company_id}/mappings/suggest")
def suggest_mappings(
    company_id: int,
    user: User = Depends(_require_roles(["org_admin", "analyst"])),
    db: Session = Depends(get_db),
):
    actuals = db.query(Actual).filter(Actual.company_id == company_id).all()
    sources = {a.category for a in actuals}
    suggestions = []
    for source in sources:
        match = next(
            (cat for cat in CANONICAL_CATEGORIES if cat.lower() in source.lower() or source.lower() in cat.lower()),
            None,
        )
        if match:
            suggestions.append({"source_account": source, "canonical_category": match})
    return {"suggestions": suggestions}


@router.get("/companies/{company_id}/mappings/status")
def mapping_status(
    company_id: int,
    user: User = Depends(_require_roles(["org_admin", "analyst"])),
    db: Session = Depends(get_db),
):
    actuals = db.query(Actual).filter(Actual.company_id == company_id).all()
    sources = {a.category for a in actuals}
    mappings = {
        m.source_account: m.canonical_category
        for m in db.query(Mapping).filter(Mapping.company_id == company_id).all()
    }
    unmapped = [source for source in sources if source not in CANONICAL_CATEGORIES and source not in mappings]
    return {"unmapped_accounts": unmapped, "mapped_count": len(mappings)}


@router.post("/companies/{company_id}/mappings")
def upsert_mapping(
    company_id: int,
    source_account: str,
    canonical_category: str,
    user: User = Depends(_require_roles(["org_admin", "analyst"])),
    db: Session = Depends(get_db),
):
    mapping = (
        db.query(Mapping)
        .filter(Mapping.company_id == company_id, Mapping.source_account == source_account)
        .first()
    )
    if mapping:
        mapping.canonical_category = canonical_category
    else:
        mapping = Mapping(
            company_id=company_id,
            source_account=source_account,
            canonical_category=canonical_category,
        )
        db.add(mapping)
    db.commit()
    _log(db, user.org_id, user.id, "mapping_updated", source_account)
    return {"status": "ok"}


@router.get("/companies/{company_id}/mappings/export")
def export_mappings(
    company_id: int,
    user: User = Depends(_require_roles(["org_admin", "analyst"])),
    db: Session = Depends(get_db),
):
    mappings = db.query(Mapping).filter(Mapping.company_id == company_id).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["source_account", "canonical_category"])
    for mapping in mappings:
        writer.writerow([mapping.source_account, mapping.canonical_category])
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
    )
    response.headers["Content-Disposition"] = "attachment; filename=mappings.csv"
    return response


@router.post("/companies/{company_id}/mappings/import")
def import_mappings(
    company_id: int,
    file: UploadFile = File(...),
    user: User = Depends(_require_roles(["org_admin", "analyst"])),
    db: Session = Depends(get_db),
):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(StringIO(content))
    if "source_account" not in reader.fieldnames or "canonical_category" not in reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV must include source_account and canonical_category")
    for row in reader:
        source_account = row["source_account"]
        canonical_category = row["canonical_category"]
        mapping = (
            db.query(Mapping)
            .filter(Mapping.company_id == company_id, Mapping.source_account == source_account)
            .first()
        )
        if mapping:
            mapping.canonical_category = canonical_category
        else:
            db.add(
                Mapping(
                    company_id=company_id,
                    source_account=source_account,
                    canonical_category=canonical_category,
                )
            )
    db.commit()
    _log(db, user.org_id, user.id, "mapping_imported", file.filename)
    return {"status": "ok"}


@router.post("/companies/{company_id}/scenarios", response_model=ScenarioOut)
def create_scenario(
    company_id: int,
    payload: ScenarioCreate,
    user: User = Depends(_require_roles(["org_admin", "analyst"])),
    db: Session = Depends(get_db),
):
    scenario = Scenario(company_id=company_id, **payload.model_dump())
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    _log(db, user.org_id, user.id, "scenario_created", scenario.name)
    return scenario


@router.get("/companies/{company_id}/pack")
def download_pack(
    company_id: int,
    user: User = Depends(_require_roles(["org_admin", "analyst", "viewer"])),
    db: Session = Depends(get_db),
):
    actuals = db.query(Actual).filter(Actual.company_id == company_id).all()
    mappings = {
        m.source_account: m.canonical_category
        for m in db.query(Mapping).filter(Mapping.company_id == company_id).all()
    }
    sources = {a.category for a in actuals}
    unmapped = [source for source in sources if source not in CANONICAL_CATEGORIES and source not in mappings]
    if unmapped:
        raise HTTPException(status_code=400, detail="Unmapped accounts present; resolve mappings before pack.")
    records = [ActualRecord(a.period, a.category, a.amount) for a in actuals]
    kpis = compute_kpis(records)
    scenario_defaults = {
        "Base": {"revenue_growth": 0.05, "gross_margin": 0.6, "opex_growth": 0.03},
        "Upside": {"revenue_growth": 0.1, "gross_margin": 0.65, "opex_growth": 0.04},
        "Downside": {"revenue_growth": -0.02, "gross_margin": 0.5, "opex_growth": 0.02},
    }
    scenario_rows = db.query(Scenario).filter(Scenario.company_id == company_id).all()
    scenario_map = {s.name: s for s in scenario_rows}
    base = scenario_map.get("Base")
    base_params = base or Scenario(company_id=company_id, name="Base", **scenario_defaults["Base"])
    forecasted = forecast(
        kpis, 12, base_params.revenue_growth, base_params.gross_margin, base_params.opex_growth
    )
    sensitivity = sensitivity_grid(
        kpis,
        revenue_growth_range=[-0.05, 0.0, 0.05],
        gross_margin_range=[0.4, 0.5, 0.6],
        opex_growth=base_params.opex_growth,
    )
    scenarios = []
    scenario_results = []
    scenario_deltas = []
    for name, defaults in scenario_defaults.items():
        scenario = scenario_map.get(name)
        params = scenario or Scenario(company_id=company_id, name=name, **defaults)
        scenario_forecast = forecast(
            kpis, 12, params.revenue_growth, params.gross_margin, params.opex_growth
        )
        latest_forecast = scenario_forecast[-1] if scenario_forecast else None
        scenarios.append(
            {
                "name": name,
                "revenue_growth": params.revenue_growth,
                "gross_margin": params.gross_margin,
                "opex_growth": params.opex_growth,
            }
        )
        scenario_results.append(
            {
                "name": name,
                "ending_revenue": latest_forecast.revenue if latest_forecast else 0.0,
                "ending_ebitda": latest_forecast.ebitda if latest_forecast else 0.0,
                "ending_runway_months": latest_forecast.runway_months if latest_forecast else 0.0,
            }
        )
    base_result = next((r for r in scenario_results if r["name"] == "Base"), None)
    for result in scenario_results:
        if base_result and result["name"] != "Base":
            scenario_deltas.append(
                {
                    "name": result["name"],
                    "delta_revenue": result["ending_revenue"] - base_result["ending_revenue"],
                    "delta_ebitda": result["ending_ebitda"] - base_result["ending_ebitda"],
                    "delta_runway_months": result["ending_runway_months"]
                    - base_result["ending_runway_months"],
                }
            )
    company = db.query(Company).get(company_id)
    excel_bytes = build_workbook(
        company.name if company else "Company",
        kpis,
        forecasted,
        scenarios,
        scenario_results,
        scenario_deltas,
        sensitivity,
    )
    _log(db, user.org_id, user.id, "pack_generated", str(company_id))
    filename = f"company_{company_id}_pack.xlsx"
    stream = BytesIO(excel_bytes)
    response = StreamingResponse(
        stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@router.get("/portfolio/dashboard")
def portfolio_dashboard(
    user: User = Depends(_require_roles(["org_admin", "analyst", "viewer"])),
    db: Session = Depends(get_db),
):
    companies = db.query(Company).filter(Company.org_id == user.org_id).all()
    summary = []
    for company in companies:
        actuals = db.query(Actual).filter(Actual.company_id == company.id).all()
        kpis = compute_kpis([ActualRecord(a.period, a.category, a.amount) for a in actuals])
        if not kpis:
            continue
        latest = kpis[-1]
        prior = kpis[-2] if len(kpis) > 1 else None
        revenue_change = (latest.revenue - prior.revenue) / prior.revenue if prior and prior.revenue else 0.0
        margin_change = latest.gross_margin - prior.gross_margin if prior else 0.0
        summary.append(
            {
                "company": company.name,
                "runway_months": latest.runway_months,
                "revenue": latest.revenue,
                "gross_margin": latest.gross_margin,
                "revenue_change": revenue_change,
                "gross_margin_change": margin_change,
            }
        )
    risks = [
        s
        for s in summary
        if s["runway_months"] < _org_setting(db, user.org_id).runway_risk_threshold
        or s["revenue_change"] < _org_setting(db, user.org_id).revenue_drop_threshold
        or s["gross_margin_change"] < _org_setting(db, user.org_id).margin_drop_threshold
    ]
    return {"summary": summary, "risks": risks}


@router.get("/audit/logs", response_model=list[AuditLogOut])
def list_audit_logs(
    action: str | None = None,
    user: User = Depends(_require_roles(["org_admin", "analyst"])),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog).filter(AuditLog.org_id == user.org_id)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.created_at.desc()).limit(200).all()


@router.get("/org/settings", response_model=OrgSettingsOut)
def get_org_settings(user: User = Depends(_require_roles(["org_admin"])), db: Session = Depends(get_db)):
    return _org_setting(db, user.org_id)


@router.put("/org/settings", response_model=OrgSettingsOut)
def update_org_settings(
    payload: OrgSettingsUpdate,
    user: User = Depends(_require_roles(["org_admin"])),
    db: Session = Depends(get_db),
):
    settings_row = db.query(OrganizationSetting).filter(OrganizationSetting.org_id == user.org_id).first()
    if not settings_row:
        settings_row = OrganizationSetting(org_id=user.org_id, **payload.model_dump())
        db.add(settings_row)
    else:
        settings_row.runway_risk_threshold = payload.runway_risk_threshold
        settings_row.revenue_drop_threshold = payload.revenue_drop_threshold
        settings_row.margin_drop_threshold = payload.margin_drop_threshold
    db.commit()
    db.refresh(settings_row)
    _log(db, user.org_id, user.id, "org_settings_updated", None)
    return settings_row


@router.get("/templates/actuals.csv")
def download_actuals_template():
    template_path = Path(__file__).resolve().parents[3] / "examples" / "csv_templates" / "actuals_template.csv"
    return FileResponse(
        path=str(template_path),
        media_type="text/csv",
        filename="actuals_template.csv",
    )
