import os
from datetime import date
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr

from database import create_document, get_documents, db
from schemas import User, Membership, Protocol, Biomarker, Signal, Shipment, Integration

app = FastAPI(title="AmazingXO API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Utilities ---------
class ApiMessage(BaseModel):
    message: str


def collection_name(model_cls) -> str:
    return model_cls.__name__.lower()


# -------- Brand/Copy ---------
BRAND_DOC: Dict[str, Any] = {
    "hero": {
        "headline": [
            "PERFORMANCE.",
            "That’s the point.",
            "That’s the promise.",
            "That’s the experience.",
        ],
        "cta": "Get Started",
        "sub": "AmazingXO is Performance.",
    },
    "how": [
        {"step": 1, "title": "Data", "desc": "Blood work."},
        {"step": 2, "title": "Choose", "desc": "Prescription. Performance. Recovery."},
        {"step": 3, "title": "Action", "desc": "Pick up prescription. Follow protocol."},
        {"step": 4, "title": "Track", "desc": "Data. Performance. Recovery."},
    ],
    "pricing": {
        "access": {"label": "Access Fee", "price": 25, "unit": "month"},
        "performance": {"label": "Performance Membership", "price": 1497, "unit": "month"},
        "alacarte": [
            {"name": "Bloodwork", "price": 397, "cycle": "every 3 months"},
            {"name": "Prescription Only", "price": 197, "cycle": "month"},
            {"name": "Nurse Phone Support", "price": 297, "cycle": "month"},
        ],
    },
    "protocols": {
        "performance": ["Energy", "Lean", "Hormones", "Libido"],
        "recovery": ["Focus", "Menopause", "Relieve", "Skin"],
    },
    "biomarkers": [
        "Testosterone",
        "Estradiol (E2)",
        "SHBG",
        "CRP",
        "Fasting Insulin",
    ],
    "performanceSignals": ["Capacity", "Power", "Speed", "Pressure", "Efficiency"],
    "recoverySignals": ["Inflammation", "Fatigue", "Electrolytes", "Lymphatic", "Glycogen"],
    "policies": {
        "privacy": {
            "title": "Privacy Policy",
            "body": "We collect only what drives performance. No resale. No noise."
        },
        "terms": {
            "title": "Terms of Service",
            "body": "Membership maintains access to the console, data, and shipments."
        },
        "refund": {
            "title": "Refund Policy",
            "body": "Access fees are monthly. Packages are service-forward and non-refundable once delivered."
        },
    },
}


@app.get("/", response_model=ApiMessage)
def read_root():
    return {"message": "AmazingXO Backend Running"}


@app.get("/api/brand")
def get_brand():
    return BRAND_DOC


# -------- Schema exposure for viewers --------
@app.get("/schema")
def get_schema_overview():
    """Expose available model names so external viewers can introspect."""
    return {
        "models": [
            "user",
            "membership",
            "protocol",
            "biomarker",
            "signal",
            "shipment",
            "integration",
        ]
    }


# -------- Membership & Users --------
class MembershipCreate(BaseModel):
    user_email: EmailStr
    plan: str = Field(..., pattern="^(access|performance)$")
    family_members: Optional[List[EmailStr]] = []


@app.post("/api/membership", response_model=ApiMessage)
def create_membership(payload: MembershipCreate):
    price = 25.0 if payload.plan == "access" else 1497.0
    mem = Membership(
        user_email=payload.user_email,
        plan=payload.plan,
        price_usd=price,
        start_date=date.today(),
        family_members=payload.family_members or [],
    )
    create_document(collection_name(Membership), mem)
    return {"message": "Membership activated"}


@app.get("/api/membership")
def list_memberships(email: Optional[EmailStr] = None):
    filt = {"user_email": str(email)} if email else {}
    return get_documents(collection_name(Membership), filt, limit=50)


# -------- Protocols --------
@app.get("/api/protocols")
def list_protocols():
    return BRAND_DOC["protocols"]


class ProtocolAssign(BaseModel):
    owner_email: EmailStr
    kind: str = Field(..., pattern="^(performance|recovery)$")
    name: str


@app.post("/api/protocols", response_model=ApiMessage)
def assign_protocol(payload: ProtocolAssign):
    proto = Protocol(kind=payload.kind, name=payload.name, owner_email=payload.owner_email)
    create_document(collection_name(Protocol), proto)
    return {"message": "Protocol added"}


@app.get("/api/protocols/assigned")
def list_assigned_protocols(owner_email: EmailStr):
    return get_documents(collection_name(Protocol), {"owner_email": str(owner_email)}, limit=50)


# -------- Biomarkers & Signals --------
class BiomarkerIn(BaseModel):
    owner_email: EmailStr
    name: str
    value: float
    unit: str
    taken_on: date


@app.post("/api/biomarkers", response_model=ApiMessage)
def add_biomarker(payload: BiomarkerIn):
    if payload.name not in BRAND_DOC["biomarkers"]:
        raise HTTPException(400, "Unknown biomarker")
    doc = Biomarker(**payload.model_dump())
    create_document(collection_name(Biomarker), doc)
    return {"message": "Biomarker logged"}


@app.get("/api/biomarkers")
def list_biomarkers(owner_email: EmailStr):
    return get_documents(collection_name(Biomarker), {"owner_email": str(owner_email)}, limit=100)


class SignalIn(BaseModel):
    owner_email: EmailStr
    domain: str
    name: str
    score: int = Field(..., ge=0, le=100)
    noted_on: date


@app.post("/api/signals", response_model=ApiMessage)
def add_signal(payload: SignalIn):
    valid = BRAND_DOC["performanceSignals"] + BRAND_DOC["recoverySignals"]
    if payload.name not in valid:
        raise HTTPException(400, "Unknown signal")
    doc = Signal(**payload.model_dump())
    create_document(collection_name(Signal), doc)
    return {"message": "Signal logged"}


@app.get("/api/signals")
def list_signals(owner_email: EmailStr):
    return get_documents(collection_name(Signal), {"owner_email": str(owner_email)}, limit=100)


# -------- Integrations --------
class IntegrationConnect(BaseModel):
    owner_email: EmailStr
    name: str
    metadata: Optional[dict] = None


@app.post("/api/integrations/connect", response_model=ApiMessage)
def connect_integration(payload: IntegrationConnect):
    integ = Integration(owner_email=payload.owner_email, name=payload.name, status="connected", metadata=payload.metadata)
    create_document(collection_name(Integration), integ)
    return {"message": "Integration connected"}


@app.get("/api/integrations")
def list_integrations(owner_email: EmailStr):
    return get_documents(collection_name(Integration), {"owner_email": str(owner_email)}, limit=50)


# -------- Shipments --------
class ShipmentCreate(BaseModel):
    owner_email: EmailStr
    item: str


@app.post("/api/shipments", response_model=ApiMessage)
def create_shipment(payload: ShipmentCreate):
    ship = Shipment(owner_email=payload.owner_email, item=payload.item)
    create_document(collection_name(Shipment), ship)
    return {"message": "Shipment queued"}


@app.get("/api/shipments")
def list_shipments(owner_email: EmailStr):
    return get_documents(collection_name(Shipment), {"owner_email": str(owner_email)}, limit=50)


# -------- AI: Simple agentic insight engine --------
class InsightRequest(BaseModel):
    owner_email: EmailStr


def score_to_word(v: float) -> str:
    if v >= 80:
        return "Prime"
    if v >= 60:
        return "Strong"
    if v >= 40:
        return "Moderate"
    return "Low"


@app.post("/api/ai/insights")
def ai_insights(req: InsightRequest):
    # Pull latest signals and biomarkers
    owner = str(req.owner_email)
    bios = get_documents(collection_name(Biomarker), {"owner_email": owner}, limit=100)
    sigs = get_documents(collection_name(Signal), {"owner_email": owner}, limit=100)

    advice: List[str] = []

    # Rule examples
    name_map = {b.get("name"): b for b in bios}
    if "CRP" in name_map and isinstance(name_map["CRP"].get("value"), (int, float)):
        crp = float(name_map["CRP"]["value"])
        if crp > 3:
            advice.append("Inflammation elevated. Shift to Recovery: Relieve. Emphasize sleep, electrolytes, and low-impact work.")
        elif crp < 1:
            advice.append("Inflammation low. Push Performance: Energy or Lean.")

    if "Fasting Insulin" in name_map and isinstance(name_map["Fasting Insulin"].get("value"), (int, float)):
        ins = float(name_map["Fasting Insulin"]["value"])
        if ins > 15:
            advice.append("Metabolic load high. Tighten feeding window. Consider Lean + Prescription review.")
        elif ins < 5:
            advice.append("Engine efficient. Maintain current protocol. Add Power work blocks.")

    # Aggregate signal scores
    domain_scores: Dict[str, List[int]] = {"performance": [], "recovery": []}
    for s in sigs:
        domain = s.get("domain", "performance")
        score = s.get("score", 50)
        try:
            score = int(score)
        except Exception:
            score = 50
        if domain in domain_scores:
            domain_scores[domain].append(score)

    perf_avg = sum(domain_scores["performance"]) / max(1, len(domain_scores["performance"]))
    rec_avg = sum(domain_scores["recovery"]) / max(1, len(domain_scores["recovery"]))

    advice.append(f"Performance: {score_to_word(perf_avg)}. Recovery: {score_to_word(rec_avg)}.")
    if perf_avg > rec_avg + 15:
        advice.append("Ceiling rising faster than the floor. Add Recovery day.")
    elif rec_avg > perf_avg + 15:
        advice.append("Floor stable. Push a Performance session.")

    return {
        "owner_email": owner,
        "biomarkers": bios,
        "signals": sigs,
        "insights": advice[:6],
    }


# -------- Policies --------
@app.get("/api/policies/{key}")
def get_policy(key: str):
    pol = BRAND_DOC.get("policies", {}).get(key)
    if not pol:
        raise HTTPException(404, "Policy not found")
    return pol


# -------- Health/Test --------
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", "Unknown")
            _ = db.list_collection_names()
            response["collections"] = _[:10]
            response["connection_status"] = "Connected"
            response["database"] = "✅ Connected & Working"
    except Exception as e:
        response["database"] = f"⚠️  Connected but Error: {str(e)[:100]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
