"""
SANDHI Cascade Engine

Deterministic disruption propagation through the itinerary dependency graph.
Uses NetworkX for graph operations. No AI/ML involved.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import networkx as nx

from app.models import (
    Booking, BookingStatus, BookingType, CascadeEffect, CascadeResult,
    Dependency, Disruption, Trip,
)


# Threshold below which a connection is considered AT_RISK (minutes)
AT_RISK_THRESHOLD_MINUTES = 15


def build_graph(trip: Trip) -> nx.DiGraph:
    """Build a directed dependency graph from a trip's bookings and dependencies."""
    g = nx.DiGraph()
    booking_map = {b.id: b for b in trip.bookings}

    for booking in trip.bookings:
        g.add_node(booking.id, booking=booking)

    for dep in trip.dependencies:
        if dep.from_booking_id in booking_map and dep.to_booking_id in booking_map:
            g.add_edge(
                dep.from_booking_id,
                dep.to_booking_id,
                dependency=dep,
            )

    return g


def get_effective_arrival(booking: Booking) -> datetime:
    """Get the effective arrival time (actual if available, otherwise scheduled)."""
    return booking.actual_arrival or booking.scheduled_arrival


def get_effective_departure(booking: Booking) -> datetime:
    """Get the effective departure time (actual if available, otherwise scheduled)."""
    return booking.actual_departure or booking.scheduled_departure


def calculate_slack(
    predecessor: Booking,
    successor: Booking,
    dep: Dependency,
) -> float:
    """
    Calculate slack in minutes between two connected bookings.

    slack = successor_departure - (predecessor_arrival + min_transfer_time)

    Positive slack means the connection is feasible.
    Negative slack means the connection is broken.
    """
    pred_arrival = get_effective_arrival(predecessor)
    succ_departure = get_effective_departure(successor)
    transfer_time = timedelta(minutes=dep.min_transfer_minutes)

    earliest_possible = pred_arrival + transfer_time
    slack = (succ_departure - earliest_possible).total_seconds() / 60.0
    return slack


def determine_status(
    booking: Booking,
    slack: float | None,
    predecessor_status: BookingStatus | None,
) -> BookingStatus:
    """
    Determine the new status of a booking based on slack and predecessor status.

    Rules (Conservative Semantics):
    - If predecessor is INFEASIBLE/MISSED → transport is MISSED; non-transport (hotel, attraction) is AT_RISK
    - If slack < 0 → INFEASIBLE for transport; AT_RISK for non-transport
    - If slack < AT_RISK_THRESHOLD → AT_RISK
    - Otherwise → current status preserved
    """
    # If predecessor is already failed, cascade conservative status
    if predecessor_status in (BookingStatus.INFEASIBLE, BookingStatus.MISSED, BookingStatus.FORFEITED):
        if booking.type in (BookingType.FLIGHT, BookingType.TRAIN, BookingType.TRANSFER):
            return BookingStatus.MISSED
        return BookingStatus.AT_RISK

    if slack is not None and slack < 0:
        if booking.type in (BookingType.FLIGHT, BookingType.TRAIN, BookingType.TRANSFER):
            return BookingStatus.INFEASIBLE
        return BookingStatus.AT_RISK

    if slack is not None and slack < AT_RISK_THRESHOLD_MINUTES:
        return BookingStatus.AT_RISK

    return booking.status


def build_explanation(
    booking: Booking,
    new_status: BookingStatus,
    slack: float | None,
    predecessor: Booking | None,
    dep: Dependency | None,
    predecessor_status: BookingStatus | None,
) -> str:
    """Build a human-readable explanation for why a booking's status changed."""
    if new_status == booking.status:
        return f"{booking.reference} remains {booking.status.value}."

    if predecessor is None:
        if new_status == BookingStatus.DELAYED:
            return f"{booking.reference} is delayed."
        return f"{booking.reference} status changed to {new_status.value}."

    pred_arrival = get_effective_arrival(predecessor)
    succ_departure = get_effective_departure(booking)
    transfer = dep.min_transfer_minutes if dep else 0

    if predecessor_status in (BookingStatus.INFEASIBLE, BookingStatus.MISSED, BookingStatus.FORFEITED):
        return (
            f"{booking.reference} is {new_status.value.replace('_', ' ')} because preceding connection "
            f"{predecessor.reference} is {predecessor_status.value.replace('_', ' ')}. "
            f"Cannot reach {booking.origin} on original schedule."
        )

    if slack is not None and slack < 0:
        return (
            f"{booking.reference} is {new_status.value.replace('_', ' ')} because "
            f"{predecessor.reference} arrives at {pred_arrival.strftime('%H:%M')} "
            f"+ {transfer} min transfer = "
            f"{(pred_arrival + timedelta(minutes=transfer)).strftime('%H:%M')}, "
            f"which is after {booking.reference} scheduled departure at "
            f"{succ_departure.strftime('%H:%M')} "
            f"(slack: {slack:.0f} min)."
        )

    if slack is not None and slack < AT_RISK_THRESHOLD_MINUTES:
        return (
            f"{booking.reference} is AT RISK because "
            f"{predecessor.reference} arrives at {pred_arrival.strftime('%H:%M')} "
            f"+ {transfer} min transfer = "
            f"{(pred_arrival + timedelta(minutes=transfer)).strftime('%H:%M')}, "
            f"leaving only {slack:.0f} min before {booking.reference} departs at "
            f"{succ_departure.strftime('%H:%M')}."
        )

    return f"{booking.reference} remains {new_status.value} with {slack:.0f} min slack."


def propagate_disruption(
    trip: Trip,
    disruption: Disruption,
) -> CascadeResult:
    """
    Propagate a disruption through the itinerary dependency graph.

    Algorithm:
    1. Apply disruption to source booking
    2. Process nodes in topological order
    3. For each node, check incoming dependencies
    4. Calculate slack and determine new status
    5. Record explanation and structured calculation breakdown for each status change

    All calculations are deterministic. No AI/ML involved.
    """
    # Build graph
    g = build_graph(trip)

    # Create mutable booking map
    booking_map = {b.id: b.model_copy() for b in trip.bookings}

    # Apply disruption to source booking
    source = booking_map[disruption.booking_id]
    if disruption.new_departure:
        source.actual_departure = disruption.new_departure
    if disruption.new_arrival:
        source.actual_arrival = disruption.new_arrival
    source.status = BookingStatus.DELAYED

    # Update node data
    g.nodes[source.id]["booking"] = source

    # Track effects
    effects: list[CascadeEffect] = []

    # Record effect for the disrupted booking itself
    effects.append(CascadeEffect(
        booking_id=source.id,
        original_status=BookingStatus.CONFIRMED,
        new_status=BookingStatus.DELAYED,
        slack_minutes=None,
        explanation=f"{source.reference} is delayed by {disruption.delay_minutes} minutes. "
                    f"New arrival: {get_effective_arrival(source).strftime('%H:%M')}.",
        affected_by=None,
        breakdown={
            "scheduled_departure": source.scheduled_departure.strftime('%H:%M'),
            "scheduled_arrival": source.scheduled_arrival.strftime('%H:%M'),
            "updated_departure": source.actual_departure.strftime('%H:%M') if source.actual_departure else None,
            "updated_arrival": source.actual_arrival.strftime('%H:%M') if source.actual_arrival else None,
            "delay_minutes": disruption.delay_minutes,
            "verdict": f"Delayed by {disruption.delay_minutes} min",
        },
    ))

    # Track status for propagation
    status_map: dict[str, BookingStatus] = {source.id: BookingStatus.DELAYED}

    # Process in topological order
    try:
        topo_order = list(nx.topological_sort(g))
    except nx.NetworkXUnfeasible:
        # Graph has a cycle — shouldn't happen with a valid itinerary
        topo_order = list(g.nodes)

    dep_map = {(d.from_booking_id, d.to_booking_id): d for d in trip.dependencies}

    for node_id in topo_order:
        if node_id == disruption.booking_id:
            continue  # Already handled

        booking = booking_map[node_id]
        predecessors = list(g.predecessors(node_id))

        if not predecessors:
            # No incoming dependencies — not affected
            status_map[node_id] = booking.status
            continue

        # Find the worst-case predecessor effect
        worst_slack: float | None = None
        worst_predecessor: Booking | None = None
        worst_dep: Dependency | None = None
        worst_pred_status: BookingStatus | None = None

        for pred_id in predecessors:
            pred_booking = booking_map[pred_id]
            dep = dep_map.get((pred_id, node_id))
            if dep is None:
                continue

            slack = calculate_slack(pred_booking, booking, dep)
            pred_status = status_map.get(pred_id, pred_booking.status)

            # Use the worst (most negative) slack
            if worst_slack is None or slack < worst_slack:
                worst_slack = slack
                worst_predecessor = pred_booking
                worst_dep = dep
                worst_pred_status = pred_status

            # If predecessor is already failed, that dominates
            if pred_status in (BookingStatus.INFEASIBLE, BookingStatus.MISSED, BookingStatus.FORFEITED):
                worst_predecessor = pred_booking
                worst_dep = dep
                worst_pred_status = pred_status

        # Determine new status
        new_status = determine_status(booking, worst_slack, worst_pred_status)

        # Update booking status
        booking.status = new_status
        status_map[node_id] = new_status

        # Build explanation
        explanation = build_explanation(
            booking, new_status, worst_slack,
            worst_predecessor, worst_dep, worst_pred_status,
        )

        # Build structured breakdown for "Why did this break?" UI
        breakdown_data = None
        if worst_predecessor and worst_dep:
            pred_arr = get_effective_arrival(worst_predecessor)
            succ_dep = get_effective_departure(booking)
            transfer_mins = worst_dep.min_transfer_minutes
            earliest_arr = pred_arr + timedelta(minutes=transfer_mins)
            breakdown_data = {
                "predecessor_reference": worst_predecessor.reference,
                "predecessor_arrival": pred_arr.strftime('%H:%M'),
                "required_transfer_minutes": transfer_mins,
                "earliest_arrival": earliest_arr.strftime('%H:%M'),
                "scheduled_departure": succ_dep.strftime('%H:%M'),
                "slack_minutes": worst_slack,
                "verdict": (
                    "Connection impossible" if (worst_slack is not None and worst_slack < 0)
                    else "Connection at risk" if (worst_slack is not None and worst_slack < AT_RISK_THRESHOLD_MINUTES)
                    else "Dependency impacted"
                ),
            }

        # Only record effect if status changed from confirmed
        if new_status != BookingStatus.CONFIRMED:
            effects.append(CascadeEffect(
                booking_id=node_id,
                original_status=BookingStatus.CONFIRMED,
                new_status=new_status,
                slack_minutes=worst_slack,
                explanation=explanation,
                affected_by=worst_predecessor.id if worst_predecessor else None,
                breakdown=breakdown_data,
            ))

    return CascadeResult(
        trip_id=trip.id,
        disruption_id=disruption.id,
        effects=effects,
        timestamp=datetime.utcnow(),
    )

