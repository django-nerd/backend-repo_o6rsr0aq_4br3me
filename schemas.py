"""
Database Schemas

AmazingXO Data Model

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import date

# Core user/account
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    role: Literal["owner","member"] = Field("owner", description="User role")
    active: bool = Field(True, description="Active account flag")

class Membership(BaseModel):
    user_email: EmailStr = Field(..., description="Linked user email")
    plan: Literal["access","performance"] = Field(..., description="Plan type")
    price_usd: float = Field(..., ge=0)
    start_date: date = Field(...)
    family_members: List[EmailStr] = Field(default_factory=list)

# Protocols
class Protocol(BaseModel):
    kind: Literal["performance","recovery"] = Field(...)
    name: str = Field(..., description="One-word name")
    status: Literal["active","paused","completed"] = Field("active")
    owner_email: EmailStr = Field(...)

# Biomarkers and Indicators
class Biomarker(BaseModel):
    owner_email: EmailStr
    name: Literal["Testosterone","Estradiol (E2)","SHBG","CRP","Fasting Insulin"]
    value: float = Field(...)
    unit: str = Field(...)
    taken_on: date

class Signal(BaseModel):
    owner_email: EmailStr
    domain: Literal["performance","recovery"]
    name: Literal["Capacity","Power","Speed","Pressure","Efficiency","Inflammation","Fatigue","Electrolytes","Lymphatic","Glycogen"]
    score: int = Field(..., ge=0, le=100)
    noted_on: date

# Logistics
class Shipment(BaseModel):
    owner_email: EmailStr
    item: Literal["Protocol Kit","Prescription","Bloodwork Kit"]
    status: Literal["queued","shipped","delivered"] = "queued"
    tracking: Optional[str] = None

class Integration(BaseModel):
    owner_email: EmailStr
    name: str
    status: Literal["connected","disconnected"] = "disconnected"
    metadata: Optional[dict] = None
