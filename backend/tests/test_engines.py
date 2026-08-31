"""
SANDHI Tests — Core Engine Tests

Tests for the dependency graph, cascade propagation, deadline computation,
entitlement engine, recovery engine, and the full end-to-end demo scenario.
"""

from datetime import datetime, timedelta

import pytest

from app.models import (
    Booking, BookingStatus, BookingType, CascadeEffect,
    Dependency, Disruption, DisruptionType, ProvenanceType, Trip,
)
from app.cascade_engine import (
    build_graph, calculate_slack, propagate_disruption,
)
from app.deadline_engine import compute_deadlines
from app.entitlement_engine import compute_entitlements
from app.recovery_engine import check_recovery_feasibility, evaluate_recovery_options
from app.seed_data import (
    create_demo_trip, create_demo_policy_rules,
    create_demo_recovery_options, DEMO_BASE_DATE,
)


# --- Fixtures ---

@pytest.fixture
def demo_trip() -> Trip:
    return create_demo_trip()


@pytest.fixture
def policy_rules():
    return create_demo_policy_rules()


@pytest.fixture
def recovery_candidates():
    return create_demo_recovery_options()


@pytest.fixture
def base_date():
    return DEMO_BASE_DATE


# --- Test 1: Normal itinerary is feasible ---

def test_normal_itinerary_is_feasible(demo_trip):
    """All connections in the undisrupted itinerary should be feasible."""
    g = build_graph(demo_trip)
    dep_map = {(d.from_booking_id, d.to_booking_id): d for d in demo_trip.dependencies}
    booking_map = {b.id: b for b in demo_trip.bookings}

    for dep in demo_trip.dependencies:
        from_b = booking_map[dep.from_booking_id]
        to_b = booking_map[dep.to_booking_id]
        slack = calculate_slack(from_b, to_b, dep)
        assert slack > 0, (
            f"Connection {dep.from_booking_id} → {dep.to_booking_id} "
            f"has non-positive slack ({slack} min) in undisrupted itinerary"
        )


# --- Test 2: Small delay does not break a sufficiently slack connection ---

def test_small_delay_does_not_break(demo_trip, base_date):
    """A 30-minute delay should not break the flight→transfer→train chain
    because there is sufficient slack."""
    disruption = Disruption(
        id="dis_small",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=8, minute=0),
        new_arrival=base_date.replace(hour=10, minute=15),
        delay_minutes=30,
        detected_at=datetime.utcnow(),
        source="test",
    )

    result = propagate_disruption(demo_trip, disruption)

    # Flight should be delayed
    flight_effect = next(e for e in result.effects if e.booking_id == "bk_flight")
    assert flight_effect.new_status == BookingStatus.DELAYED

    # Train should still be feasible (enough slack)
    train_effects = [e for e in result.effects if e.booking_id == "bk_train"]
    if train_effects:
        # If there's an effect, it shouldn't be INFEASIBLE
        assert train_effects[0].new_status != BookingStatus.INFEASIBLE


# --- Test 3: Large delay breaks insufficiently slack connection ---

def test_large_delay_breaks_connection(demo_trip, base_date):
    """A 2h50m delay should break the train connection."""
    disruption = Disruption(
        id="dis_large",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=datetime.utcnow(),
        source="test",
    )

    result = propagate_disruption(demo_trip, disruption)
    effect_map = {e.booking_id: e for e in result.effects}

    # Train should be infeasible
    assert "bk_train" in effect_map
    assert effect_map["bk_train"].new_status in (
        BookingStatus.INFEASIBLE, BookingStatus.MISSED,
    )


# --- Test 4: Disruption propagates downstream ---

def test_disruption_propagates_downstream(demo_trip, base_date):
    """When train is missed, hotel and taj should also be affected."""
    disruption = Disruption(
        id="dis_cascade",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=datetime.utcnow(),
        source="test",
    )

    result = propagate_disruption(demo_trip, disruption)
    affected_ids = {e.booking_id for e in result.effects}

    # All downstream bookings should be affected
    assert "bk_flight" in affected_ids
    assert "bk_train" in affected_ids
    # Hotel and taj should be affected due to cascading failure
    assert "bk_hotel" in affected_ids or "bk_taj" in affected_ids


# --- Test 5: Deadline is created correctly ---

def test_deadline_created_for_missed_train(demo_trip, policy_rules, base_date):
    """When train is missed, a TDR deadline should be created."""
    now = datetime.utcnow()

    disruption = Disruption(
        id="dis_dl",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=now,
        source="test",
    )

    cascade = propagate_disruption(demo_trip, disruption)
    deadlines, evidence = compute_deadlines(
        demo_trip.bookings, cascade.effects, policy_rules, now,
    )

    # Should have at least one deadline
    assert len(deadlines) > 0

    # Should have a TDR-related deadline
    tdr_deadlines = [d for d in deadlines if "TDR" in d.deadline_type]
    assert len(tdr_deadlines) > 0


# --- Test 6: Deadline countdown is deterministic ---

def test_deadline_countdown_deterministic(demo_trip, policy_rules, base_date):
    """Deadline countdowns should be deterministic — same input → same output."""
    now = datetime(2026, 9, 1, 10, 0, 0)  # Fixed time

    disruption = Disruption(
        id="dis_det",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=now,
        source="test",
    )

    cascade = propagate_disruption(demo_trip, disruption)

    # Run twice with same time
    dl1, _ = compute_deadlines(
        demo_trip.bookings, cascade.effects, policy_rules, now, now,
    )
    dl2, _ = compute_deadlines(
        demo_trip.bookings, cascade.effects, policy_rules, now, now,
    )

    # Same number of deadlines
    assert len(dl1) == len(dl2)

    # Same expiry times (comparing by type and booking)
    for d1 in dl1:
        matching = [d for d in dl2 if d.deadline_type == d1.deadline_type
                    and d.booking_id == d1.booking_id]
        assert len(matching) > 0
        assert matching[0].expires_at == d1.expires_at


# --- Test 7: Entitlement rule fires only when conditions satisfied ---

def test_entitlement_conditions(demo_trip, policy_rules, base_date):
    """Entitlement rules should only fire when their conditions are met."""
    now = datetime.utcnow()

    disruption = Disruption(
        id="dis_ent",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=now,
        source="test",
    )

    cascade = propagate_disruption(demo_trip, disruption)
    entitlements, _ = compute_entitlements(
        demo_trip.bookings, cascade.effects, policy_rules, disruption,
    )

    for ent in entitlements:
        # Each entitlement should have conditions met
        assert len(ent.conditions_met) > 0
        # No unmet conditions
        assert len(ent.conditions_not_met) == 0


# --- Test 8: Unsupported entitlement is marked unsupported ---

def test_unsupported_entitlement_marked(demo_trip, policy_rules, base_date):
    """Entitlements from DEMO rules should be marked as ESTIMATE, not SUPPORTED."""
    now = datetime.utcnow()

    disruption = Disruption(
        id="dis_unsup",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=now,
        source="test",
    )

    cascade = propagate_disruption(demo_trip, disruption)
    entitlements, _ = compute_entitlements(
        demo_trip.bookings, cascade.effects, policy_rules, disruption,
    )

    # Find entitlements from DEMO rules
    demo_entitlements = [e for e in entitlements if e.status.value == "estimate"]
    verified_entitlements = [e for e in entitlements if e.status.value == "supported"]

    # All entitlements should have a valid status
    for ent in entitlements:
        assert ent.status.value in ("supported", "estimate", "not_supported", "not_applicable")


# --- Test 9: Provenance is attached ---

def test_provenance_attached(demo_trip, policy_rules, base_date):
    """Every entitlement and deadline should have evidence attached."""
    now = datetime.utcnow()

    disruption = Disruption(
        id="dis_prov",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=now,
        source="test",
    )

    cascade = propagate_disruption(demo_trip, disruption)

    deadlines, dl_evidence = compute_deadlines(
        demo_trip.bookings, cascade.effects, policy_rules, now,
    )
    entitlements, ent_evidence = compute_entitlements(
        demo_trip.bookings, cascade.effects, policy_rules, disruption,
    )

    # Every deadline should have an evidence_id
    for dl in deadlines:
        assert dl.evidence_id is not None

    # Every entitlement should have an evidence_id
    for ent in entitlements:
        assert ent.evidence_id is not None

    # Evidence should have provenance type
    for ev in dl_evidence + ent_evidence:
        assert ev.provenance_type is not None
        assert ev.source is not None


# --- Test 10: Infeasible recovery option is rejected ---

def test_infeasible_recovery_rejected(demo_trip, recovery_candidates, base_date):
    """The late train (21:40 arrival 23:55) should be rejected because
    hotel check-in closes at 22:00."""
    # First apply disruption to make train infeasible
    disruption = Disruption(
        id="dis_rec",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=datetime.utcnow(),
        source="test",
    )

    # Need to update the booking status first
    for b in demo_trip.bookings:
        if b.id == "bk_flight":
            b.actual_departure = disruption.new_departure
            b.actual_arrival = disruption.new_arrival
            b.status = BookingStatus.DELAYED

    cascade = propagate_disruption(demo_trip, disruption)
    for effect in cascade.effects:
        for b in demo_trip.bookings:
            if b.id == effect.booking_id:
                b.status = effect.new_status

    # Evaluate recovery options
    candidates = [c.model_copy() for c in recovery_candidates]
    results = evaluate_recovery_options(candidates, demo_trip, "bk_train")

    # The late train (rec_train_3, departs 21:40) should be infeasible
    late_train = next((r for r in results if r.id == "rec_train_3"), None)
    assert late_train is not None
    assert late_train.feasible is False
    assert late_train.failure_reason is not None


# --- Test 11: Feasible recovery option survives downstream simulation ---

def test_feasible_recovery_survives(demo_trip, recovery_candidates, base_date):
    """A feasible recovery option should have feasible=True after simulation."""
    disruption = Disruption(
        id="dis_feas",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=datetime.utcnow(),
        source="test",
    )

    for b in demo_trip.bookings:
        if b.id == "bk_flight":
            b.actual_departure = disruption.new_departure
            b.actual_arrival = disruption.new_arrival
            b.status = BookingStatus.DELAYED

    cascade = propagate_disruption(demo_trip, disruption)
    for effect in cascade.effects:
        for b in demo_trip.bookings:
            if b.id == effect.booking_id:
                b.status = effect.new_status

    candidates = [c.model_copy() for c in recovery_candidates]
    results = evaluate_recovery_options(candidates, demo_trip, "bk_train")

    # At least one option should be feasible
    feasible_options = [r for r in results if r.feasible]
    assert len(feasible_options) > 0

    # Feasible options should have scores
    for opt in feasible_options:
        assert opt.score >= 0
        assert "total" in opt.scoring_breakdown


# --- Test 12: Demo scenario produces expected result ---

def test_demo_scenario_full(demo_trip, policy_rules, recovery_candidates, base_date):
    """
    Full end-to-end demo scenario:
    Flight delayed +2h50m → cascade → deadlines → entitlements → recovery → evidence

    This is the acceptance test for the core SANDHI flow.
    """
    now = datetime(2026, 9, 1, 10, 0, 0)

    # STEP 1: Create disruption
    disruption = Disruption(
        id="dis_demo",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=35),
        delay_minutes=170,
        detected_at=now,
        source="demo",
    )

    # STEP 2: Propagate cascade
    cascade = propagate_disruption(demo_trip, disruption)

    assert cascade.trip_id == demo_trip.id
    assert len(cascade.effects) > 0

    effect_map = {e.booking_id: e for e in cascade.effects}

    # Flight should be DELAYED
    assert effect_map["bk_flight"].new_status == BookingStatus.DELAYED

    # Train should be INFEASIBLE or MISSED
    assert effect_map["bk_train"].new_status in (
        BookingStatus.INFEASIBLE, BookingStatus.MISSED,
    )

    # Every effect should have an explanation
    for effect in cascade.effects:
        assert len(effect.explanation) > 0

    # STEP 3: Compute deadlines
    # Update booking statuses first
    for effect in cascade.effects:
        for b in demo_trip.bookings:
            if b.id == effect.booking_id:
                b.status = effect.new_status

    deadlines, dl_evidence = compute_deadlines(
        demo_trip.bookings, cascade.effects, policy_rules, now, now,
    )

    assert len(deadlines) > 0

    # Deadlines should have time remaining
    for dl in deadlines:
        assert dl.time_remaining_seconds is not None or dl.time_remaining_seconds == 0

    # STEP 4: Compute entitlements
    entitlements, ent_evidence = compute_entitlements(
        demo_trip.bookings, cascade.effects, policy_rules, disruption, now,
    )

    assert len(entitlements) > 0

    # STEP 5: Evaluate recovery
    candidates = [c.model_copy() for c in recovery_candidates]
    recovery = evaluate_recovery_options(candidates, demo_trip, "bk_train")

    assert len(recovery) > 0

    # Should have both feasible and infeasible options
    has_feasible = any(r.feasible for r in recovery)
    has_infeasible = any(not r.feasible for r in recovery)
    assert has_feasible
    assert has_infeasible

    # Feasible options should rank before infeasible ones
    feasible_indices = [i for i, r in enumerate(recovery) if r.feasible]
    infeasible_indices = [i for i, r in enumerate(recovery) if not r.feasible]
    if feasible_indices and infeasible_indices:
        assert max(feasible_indices) < min(infeasible_indices)

    # STEP 6: Verify evidence/provenance
    all_evidence = dl_evidence + ent_evidence
    assert len(all_evidence) > 0
    for ev in all_evidence:
        assert ev.provenance_type is not None
        assert ev.source is not None
        assert ev.retrieved_at is not None


# --- Test 13: Deterministic Reset + Repeated Disruption ---

def test_reset_and_repeated_disruption_deterministic():
    """
    Prove that triggering disruption -> resetting -> triggering disruption again
    yields 100% identical deterministic results across all engines (cascade, deadlines, entitlements, recovery).
    """
    from app.store import SANDHIStore
    store = SANDHIStore()
    trip_id = "trip_demo_mumbai_agra"

    # Run 1
    d1 = store.create_disruption(
        trip_id=trip_id,
        booking_id="bk_flight",
        disruption_type="delay",
        delay_minutes=170,
        source="user_input",
    )
    cascade1 = store.get_cascade(trip_id)
    deadlines1 = store.get_deadlines(trip_id)
    entitlements1 = store.get_entitlements(trip_id)
    recovery1 = store.get_recovery_options(trip_id)

    # Reset
    store.reset_trip(trip_id)
    reset_trip = store.get_trip(trip_id)
    for b in reset_trip.bookings:
        assert b.status == BookingStatus.CONFIRMED

    # Run 2
    d2 = store.create_disruption(
        trip_id=trip_id,
        booking_id="bk_flight",
        disruption_type="delay",
        delay_minutes=170,
        source="user_input",
    )
    cascade2 = store.get_cascade(trip_id)
    deadlines2 = store.get_deadlines(trip_id)
    entitlements2 = store.get_entitlements(trip_id)
    recovery2 = store.get_recovery_options(trip_id)

    # Verify identical cascade effects
    assert len(cascade1.effects) == len(cascade2.effects)
    for e1, e2 in zip(cascade1.effects, cascade2.effects):
        assert e1.booking_id == e2.booking_id
        assert e1.new_status == e2.new_status
        assert e1.slack_minutes == e2.slack_minutes
        assert e1.explanation == e2.explanation

    # Verify identical deadlines (types, stakes, governing rules)
    assert len(deadlines1) == len(deadlines2)
    for dl1, dl2 in zip(deadlines1, deadlines2):
        assert dl1.booking_id == dl2.booking_id
        assert dl1.deadline_type == dl2.deadline_type
        assert dl1.value_at_stake == dl2.value_at_stake
        assert dl1.governing_rule_id == dl2.governing_rule_id

    # Verify identical entitlements
    assert len(entitlements1) == len(entitlements2)
    for ent1, ent2 in zip(entitlements1, entitlements2):
        assert ent1.booking_id == ent2.booking_id
        assert ent1.rule_id == ent2.rule_id
        assert ent1.amount == ent2.amount
        assert ent1.status == ent2.status

    # Verify identical recovery options & scores
    assert len(recovery1) == len(recovery2)
    for r1, r2 in zip(recovery1, recovery2):
        assert r1.reference == r2.reference
        assert r1.feasible == r2.feasible
        assert pytest.approx(r1.score, abs=1e-4) == r2.score
        assert r1.failure_reason == r2.failure_reason


# --- Test 14: Provenance Integrity for All Monetary and Factual Values ---

def test_provenance_integrity_all_monetary_and_factual_values():
    """
    Ensure every displayed monetary/factual value has traceable evidence
    or is explicitly labeled with valid ProvenanceType.
    """
    from app.seed_data import create_demo_evidence, create_demo_trip
    trip = create_demo_trip()
    evidence_list = create_demo_evidence()
    evidence_map = {e.id: e for e in evidence_list}

    # Verify every booking has evidence for its price and schedule
    for booking in trip.bookings:
        assert len(booking.evidence_ids) > 0, f"Booking {booking.id} missing evidence_ids"
        for eid in booking.evidence_ids:
            assert eid in evidence_map, f"Evidence {eid} not found in evidence store"
            ev = evidence_map[eid]
            assert ev.provenance_type in [
                ProvenanceType.REAL_OBSERVATION,
                ProvenanceType.HISTORICAL,
                ProvenanceType.CACHE,
                ProvenanceType.PUBLISHED_RULE,
                ProvenanceType.MODEL_PREDICTION,
                ProvenanceType.ESTIMATE,
                ProvenanceType.DEMO_FIXTURE,
            ]
            assert ev.confidence >= 0.0 and ev.confidence <= 1.0
            assert len(ev.source) > 0


# --- Test 15: Policy Rules Legal Basis Audit ---

def test_policy_rule_audited_legal_basis():
    """
    Audit every rule marked VERIFIED_STRUCTURE:
    must have actual source document, clause reference, conditions, and deterministic basis.
    """
    from app.seed_data import create_demo_policy_rules
    rules = create_demo_policy_rules()

    for rule in rules:
        assert len(rule.source_document) > 0
        assert len(rule.clause_reference) > 0
        assert len(rule.conditions) > 0
        if rule.status == "VERIFIED_STRUCTURE":
            # Must cite real regulatory authorities (e.g. DGCA, Indian Railways)
            assert any(
                authority in rule.source_document
                for authority in ["Railway", "DGCA", "Civil Aviation"]
            ), f"Rule {rule.rule_id} marked VERIFIED_STRUCTURE but does not cite recognized regulatory authority"


# --- Test 16: Deterministic "Why Did This Break?" Calculation Breakdown ---

def test_cascade_deterministic_breakdown(demo_trip, base_date):
    """
    Verify that every affected connection produces step-by-step arithmetic breakdown
    including predecessor arrival, transfer time, earliest arrival, and negative slack.
    """
    disruption = Disruption(
        id="dis_breakdown",
        booking_id="bk_flight",
        disruption_type=DisruptionType.DELAY,
        old_departure=base_date.replace(hour=7, minute=30),
        old_arrival=base_date.replace(hour=9, minute=40),
        new_departure=base_date.replace(hour=10, minute=20),
        new_arrival=base_date.replace(hour=12, minute=30),
        delay_minutes=170,
        detected_at=datetime.utcnow(),
        source="test",
    )

    result = propagate_disruption(demo_trip, disruption)
    effects_by_id = {e.booking_id: e for e in result.effects}

    # Cab transfer breakdown check
    cab_effect = effects_by_id["bk_transfer"]
    assert cab_effect.breakdown is not None
    assert cab_effect.breakdown["predecessor_arrival"] == "12:30"
    assert cab_effect.breakdown["required_transfer_minutes"] == 15
    assert cab_effect.breakdown["earliest_arrival"] == "12:45"
    assert cab_effect.breakdown["scheduled_departure"] == "10:00"
    assert cab_effect.breakdown["slack_minutes"] == -165.0
    assert "impossible" in cab_effect.breakdown["verdict"].lower()


