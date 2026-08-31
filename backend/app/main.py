"""
SANDHI — FastAPI Application

REST API for the SANDHI travel disruption cascade system.
All endpoints return domain objects validated by Pydantic.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    BookingStatus, CascadeResult, Deadline, DisruptionRequest,
    Entitlement, Evidence, GraphEdge, GraphNode, GraphResponse,
    HealthResponse, RecoveryOption, Trip,
)
from app.store import store
from app.cascade_engine import build_graph, calculate_slack


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — seed data is loaded in DataStore.__init__."""
    yield


app = FastAPI(
    title="SANDHI API",
    description="Travel Disruption Cascade Intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if "*" not in cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()


# --- Health ---

@router.get("/health", response_model=HealthResponse)
def health():
    mode = os.environ.get("SANDHI_MODE", "demo")
    return HealthResponse(status="ok", mode=mode, version="0.1.0")


# --- Trips ---

@router.get("/trips", response_model=list[Trip])
def list_trips():
    return store.list_trips()


@router.get("/trips/{trip_id}", response_model=Trip)
def get_trip(trip_id: str):
    trip = store.get_trip(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.post("/trips/{trip_id}/reset")
def reset_trip(trip_id: str):
    if not store.reset_trip(trip_id):
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"status": "reset", "trip_id": trip_id}


# --- Graph ---

@router.get("/trips/{trip_id}/graph", response_model=GraphResponse)
def get_graph(trip_id: str):
    trip = store.get_trip(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    g = build_graph(trip)
    dep_map = {(d.from_booking_id, d.to_booking_id): d for d in trip.dependencies}

    nodes = [
        GraphNode(id=b.id, booking=b, status=b.status)
        for b in trip.bookings
    ]

    edges = []
    for dep in trip.dependencies:
        from_booking = next((b for b in trip.bookings if b.id == dep.from_booking_id), None)
        to_booking = next((b for b in trip.bookings if b.id == dep.to_booking_id), None)
        slack = None
        if from_booking and to_booking:
            slack = round(calculate_slack(from_booking, to_booking, dep), 1)
        edges.append(GraphEdge(
            from_id=dep.from_booking_id,
            to_id=dep.to_booking_id,
            min_transfer_minutes=dep.min_transfer_minutes,
            transfer_location=dep.transfer_location,
            slack_minutes=slack,
        ))

    return GraphResponse(trip_id=trip_id, nodes=nodes, edges=edges)


# --- Disruptions ---

@router.post("/trips/{trip_id}/disruptions")
def create_disruption(trip_id: str, request: DisruptionRequest):
    disruption = store.create_disruption(
        trip_id=trip_id,
        booking_id=request.booking_id,
        disruption_type=request.disruption_type,
        delay_minutes=request.delay_minutes,
        source=request.source,
    )
    if disruption is None:
        raise HTTPException(status_code=404, detail="Trip or booking not found")
    return disruption


@router.get("/trips/{trip_id}/disruptions")
def get_disruptions(trip_id: str):
    return store.get_disruptions(trip_id)


# --- Cascade ---

@router.get("/trips/{trip_id}/cascade")
def get_cascade(trip_id: str):
    cascade = store.get_cascade(trip_id)
    if cascade is None:
        return {"trip_id": trip_id, "effects": [], "message": "No disruption has been triggered yet."}
    return cascade


# --- Deadlines ---

@router.get("/trips/{trip_id}/deadlines", response_model=list[Deadline])
def get_deadlines(trip_id: str):
    return store.get_deadlines(trip_id)


# --- Entitlements ---

@router.get("/trips/{trip_id}/entitlements", response_model=list[Entitlement])
def get_entitlements(trip_id: str):
    return store.get_entitlements(trip_id)


# --- Recovery Options ---

@router.get("/trips/{trip_id}/recovery-options", response_model=list[RecoveryOption])
def get_recovery_options(trip_id: str):
    return store.get_recovery_options(trip_id)


# --- Evidence ---

@router.get("/evidence/{evidence_id}", response_model=Evidence)
def get_evidence(evidence_id: str):
    ev = store.get_evidence(evidence_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev


@router.get("/evidence", response_model=list[Evidence])
def list_evidence():
    return list(store.evidence.values())


# Register routes at both root and /api for seamless local + Vercel routing
app.include_router(router)
app.include_router(router, prefix="/api")

