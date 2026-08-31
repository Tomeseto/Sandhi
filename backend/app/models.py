"""
SANDHI Domain Models

All core domain types used across the application.
Every critical value carries provenance metadata.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Enums ---

class BookingType(str, Enum):
    FLIGHT = "flight"
    TRAIN = "train"
    TRANSFER = "transfer"
    HOTEL = "hotel"
    ATTRACTION = "attraction"


class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    DELAYED = "delayed"
    AT_RISK = "at_risk"
    INFEASIBLE = "infeasible"
    MISSED = "missed"
    FORFEITED = "forfeited"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class ProvenanceType(str, Enum):
    REAL_OBSERVATION = "REAL_OBSERVATION"
    HISTORICAL = "HISTORICAL"
    CACHE = "CACHE"
    PUBLISHED_RULE = "PUBLISHED_RULE"
    MODEL_PREDICTION = "MODEL_PREDICTION"
    ESTIMATE = "ESTIMATE"
    DEMO_FIXTURE = "DEMO_FIXTURE"


class DisruptionType(str, Enum):
    DELAY = "delay"
    CANCELLATION = "cancellation"


class DeadlineStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    ACTED_UPON = "acted_upon"
    NOT_APPLICABLE = "not_applicable"


class EntitlementStatus(str, Enum):
    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"
    ESTIMATE = "estimate"
    NOT_APPLICABLE = "not_applicable"


# --- Evidence / Provenance ---

class Evidence(BaseModel):
    id: str
    value: Any = None
    unit: Optional[str] = None
    provenance_type: ProvenanceType
    source: str
    retrieved_at: datetime
    source_reference: Optional[str] = None
    confidence: float = 1.0
    description: Optional[str] = None


# --- Core Domain ---

class Booking(BaseModel):
    id: str
    type: BookingType
    provider: str
    reference: str
    origin: str
    destination: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    price: float
    currency: str = "INR"
    status: BookingStatus = BookingStatus.CONFIRMED
    metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)


class Dependency(BaseModel):
    id: str
    from_booking_id: str
    to_booking_id: str
    min_transfer_minutes: int
    transfer_location: str
    calculation_source: str


class Disruption(BaseModel):
    id: str
    booking_id: str
    disruption_type: DisruptionType
    old_departure: Optional[datetime] = None
    old_arrival: Optional[datetime] = None
    new_departure: Optional[datetime] = None
    new_arrival: Optional[datetime] = None
    delay_minutes: int
    detected_at: datetime
    source: str
    evidence_id: Optional[str] = None


class Trip(BaseModel):
    id: str
    name: str
    description: str
    bookings: list[Booking] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)


# --- Cascade ---

class CascadeEffect(BaseModel):
    """Result of disruption propagation for a single booking."""
    booking_id: str
    original_status: BookingStatus
    new_status: BookingStatus
    slack_minutes: Optional[float] = None
    explanation: str
    affected_by: Optional[str] = None  # ID of the booking that caused this effect
    breakdown: Optional[dict[str, Any]] = None  # Structured calculation details



class CascadeResult(BaseModel):
    """Full cascade analysis for a trip."""
    trip_id: str
    disruption_id: str
    effects: list[CascadeEffect]
    timestamp: datetime


# --- Policy & Entitlements ---

class PolicyCondition(BaseModel):
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in
    value: Any


class PolicyResult(BaseModel):
    entitlement_type: str
    description: str
    amount_formula: Optional[str] = None
    fixed_amount: Optional[float] = None


class PolicyRule(BaseModel):
    rule_id: str
    domain: str  # railway, aviation, hotel, attraction
    trigger: str  # DELAY, CANCELLATION, MISSED_CONNECTION, etc.
    conditions: list[PolicyCondition] = Field(default_factory=list)
    result: PolicyResult
    source_document: str
    clause_reference: str
    effective_from: str
    effective_to: Optional[str] = None
    status: str = "VERIFIED_STRUCTURE"  # VERIFIED_STRUCTURE, NOT_VERIFIED, DEMO


# --- Deadline ---

class Deadline(BaseModel):
    id: str
    booking_id: str
    deadline_type: str
    description: str
    starts_at: datetime
    expires_at: datetime
    value_at_stake: Optional[float] = None
    currency: str = "INR"
    status: DeadlineStatus = DeadlineStatus.ACTIVE
    governing_rule_id: Optional[str] = None
    evidence_id: Optional[str] = None
    time_remaining_seconds: Optional[float] = None


# --- Entitlement ---

class Entitlement(BaseModel):
    id: str
    booking_id: str
    rule_id: str
    entitlement_type: str
    description: str
    amount: Optional[float] = None
    currency: str = "INR"
    status: EntitlementStatus
    evidence_id: Optional[str] = None
    conditions_met: list[str] = Field(default_factory=list)
    conditions_not_met: list[str] = Field(default_factory=list)


# --- Recovery ---

class RecoveryOption(BaseModel):
    id: str
    mode: str  # train, flight, bus, etc.
    provider: str
    reference: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    price: Optional[float] = None
    currency: str = "INR"
    source: str
    source_provenance: ProvenanceType = ProvenanceType.DEMO_FIXTURE
    feasible: bool
    failure_reason: Optional[str] = None
    score: float = 0.0
    scoring_breakdown: dict[str, float] = Field(default_factory=dict)
    downstream_effects: list[CascadeEffect] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


# --- API Request/Response ---

class DisruptionRequest(BaseModel):
    booking_id: str
    disruption_type: DisruptionType = DisruptionType.DELAY
    delay_minutes: int
    source: str = "user_input"


class HealthResponse(BaseModel):
    status: str = "ok"
    mode: str = "demo"
    version: str = "0.1.0"


class GraphNode(BaseModel):
    id: str
    booking: Booking
    status: BookingStatus


class GraphEdge(BaseModel):
    from_id: str
    to_id: str
    min_transfer_minutes: int
    transfer_location: str
    slack_minutes: Optional[float] = None


class GraphResponse(BaseModel):
    trip_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
