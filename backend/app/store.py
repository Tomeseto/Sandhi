"""
SANDHI Data Store

In-memory store backed by demo seed data.
Provides a clean repository abstraction that can be swapped to PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.models import (
    Booking, BookingStatus, BookingType, CascadeResult, Deadline,
    Disruption, DisruptionType, Entitlement, Evidence,
    PolicyRule, ProvenanceType, RecoveryOption, Trip,
)
from app.seed_data import (
    create_demo_evidence, create_demo_policy_rules,
    create_demo_recovery_options, create_demo_trip,
)
from app.cascade_engine import propagate_disruption
from app.deadline_engine import compute_deadlines
from app.entitlement_engine import compute_entitlements
from app.recovery_engine import evaluate_recovery_options


class DataStore:
    """
    In-memory data store seeded with demo data.
    All state is lost on restart — appropriate for MVP demo.
    """

    def __init__(self):
        self.trips: dict[str, Trip] = {}
        self.disruptions: dict[str, list[Disruption]] = {}  # trip_id -> disruptions
        self.cascade_results: dict[str, CascadeResult] = {}  # trip_id -> latest cascade
        self.deadlines: dict[str, list[Deadline]] = {}  # trip_id -> deadlines
        self.entitlements: dict[str, list[Entitlement]] = {}  # trip_id -> entitlements
        self.recovery_options: dict[str, list[RecoveryOption]] = {}  # trip_id -> options
        self.evidence: dict[str, Evidence] = {}  # evidence_id -> evidence
        self.policy_rules: list[PolicyRule] = []
        self._recovery_candidates: list[RecoveryOption] = []

        self._seed()

    def _seed(self):
        """Load demo seed data."""
        # Load trip
        trip = create_demo_trip()
        self.trips[trip.id] = trip

        # Load evidence
        for ev in create_demo_evidence():
            self.evidence[ev.id] = ev

        # Load policy rules
        self.policy_rules = create_demo_policy_rules()

        # Load recovery candidates
        self._recovery_candidates = create_demo_recovery_options()

    def get_trip(self, trip_id: str) -> Optional[Trip]:
        return self.trips.get(trip_id)

    def list_trips(self) -> list[Trip]:
        return list(self.trips.values())

    def get_disruptions(self, trip_id: str) -> list[Disruption]:
        return self.disruptions.get(trip_id, [])

    def create_disruption(
        self,
        trip_id: str,
        booking_id: str,
        disruption_type: DisruptionType,
        delay_minutes: int,
        source: str = "user_input",
    ) -> Disruption | None:
        """Create a disruption and compute cascade, deadlines, entitlements, recovery."""
        trip = self.trips.get(trip_id)
        if trip is None:
            return None

        booking_map = {b.id: b for b in trip.bookings}
        booking = booking_map.get(booking_id)
        if booking is None:
            return None

        now = datetime.utcnow()

        # Create disruption
        disruption = Disruption(
            id=f"dis_{booking_id}_{delay_minutes}",
            booking_id=booking_id,
            disruption_type=disruption_type,
            old_departure=booking.scheduled_departure,
            old_arrival=booking.scheduled_arrival,
            new_departure=booking.scheduled_departure + timedelta(minutes=delay_minutes),
            new_arrival=booking.scheduled_arrival + timedelta(minutes=delay_minutes),
            delay_minutes=delay_minutes,
            detected_at=now,
            source=source,
        )

        # Store disruption
        if trip_id not in self.disruptions:
            self.disruptions[trip_id] = []
        self.disruptions[trip_id].append(disruption)

        # Create evidence for disruption
        self.evidence[f"ev_disruption_{disruption.id}"] = Evidence(
            id=f"ev_disruption_{disruption.id}",
            value=delay_minutes,
            unit="minutes",
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source=source,
            retrieved_at=now,
            source_reference="User-triggered disruption in demo mode",
            confidence=1.0,
            description=f"Flight delay of {delay_minutes} minutes",
        )

        # Update booking in trip
        booking.actual_departure = disruption.new_departure
        booking.actual_arrival = disruption.new_arrival
        booking.status = BookingStatus.DELAYED

        # Propagate cascade
        cascade = propagate_disruption(trip, disruption)
        self.cascade_results[trip_id] = cascade

        # Update booking statuses from cascade effects
        for effect in cascade.effects:
            for b in trip.bookings:
                if b.id == effect.booking_id:
                    b.status = effect.new_status

        # Compute deadlines
        deadlines, deadline_evidence = compute_deadlines(
            trip.bookings, cascade.effects, self.policy_rules, now,
        )
        self.deadlines[trip_id] = deadlines
        for ev in deadline_evidence:
            self.evidence[ev.id] = ev

        # Compute entitlements
        entitlements, ent_evidence = compute_entitlements(
            trip.bookings, cascade.effects, self.policy_rules, disruption,
        )
        self.entitlements[trip_id] = entitlements
        for ev in ent_evidence:
            self.evidence[ev.id] = ev

        # Evaluate recovery options
        # Find the first infeasible/missed transport booking to replace
        replaced_id = None
        for effect in cascade.effects:
            if effect.new_status in (BookingStatus.INFEASIBLE, BookingStatus.MISSED):
                b = booking_map.get(effect.booking_id)
                if b and b.type in (BookingType.TRAIN, BookingType.FLIGHT):
                    replaced_id = effect.booking_id
                    break

        if replaced_id:
            candidates = [c.model_copy() for c in self._recovery_candidates]
            recovery = evaluate_recovery_options(candidates, trip, replaced_id)
            self.recovery_options[trip_id] = recovery
        else:
            self.recovery_options[trip_id] = []

        return disruption

    def get_cascade(self, trip_id: str) -> Optional[CascadeResult]:
        return self.cascade_results.get(trip_id)

    def get_deadlines(self, trip_id: str) -> list[Deadline]:
        deadlines = self.deadlines.get(trip_id, [])
        # Update time remaining
        now = datetime.utcnow()
        for dl in deadlines:
            remaining = (dl.expires_at - now).total_seconds()
            dl.time_remaining_seconds = max(0, remaining)
            if remaining <= 0:
                dl.status = "expired"
        return deadlines

    def get_entitlements(self, trip_id: str) -> list[Entitlement]:
        return self.entitlements.get(trip_id, [])

    def get_recovery_options(self, trip_id: str) -> list[RecoveryOption]:
        return self.recovery_options.get(trip_id, [])

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        return self.evidence.get(evidence_id)

    def reset_trip(self, trip_id: str) -> bool:
        """Reset a trip to its original state (for demo purposes)."""
        if trip_id not in self.trips:
            return False

        # Re-seed
        trip = create_demo_trip()
        self.trips[trip_id] = trip
        self.disruptions.pop(trip_id, None)
        self.cascade_results.pop(trip_id, None)
        self.deadlines.pop(trip_id, None)
        self.entitlements.pop(trip_id, None)
        self.recovery_options.pop(trip_id, None)

        return True


# Global singleton
store = DataStore()
SANDHIStore = DataStore

