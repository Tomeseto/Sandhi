"""
SANDHI Recovery Engine

Generates, feasibility-checks, and ranks recovery options.
Every candidate is inserted into the itinerary graph and downstream
effects are re-simulated to verify feasibility.
No AI/ML involved.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.cascade_engine import (
    build_graph, calculate_slack, get_effective_arrival,
    AT_RISK_THRESHOLD_MINUTES,
)
from app.models import (
    Booking, BookingStatus, BookingType, CascadeEffect,
    Dependency, RecoveryOption, Trip,
)


# Scoring weights
W_TIME = 0.4       # Weight for time efficiency
W_COST = 0.3       # Weight for cost
W_DISRUPTION = 0.2 # Weight for downstream disruption minimization
W_FEASIBILITY = 0.1  # Bonus for maintaining all downstream bookings


def check_recovery_feasibility(
    option: RecoveryOption,
    trip: Trip,
    replaced_booking_id: str,
) -> tuple[bool, str | None, list[CascadeEffect]]:
    """
    Check whether a recovery option is feasible by simulating it
    in the itinerary graph.

    Steps:
    1. Clone the itinerary
    2. Replace the affected booking with the recovery option
    3. Re-check all downstream dependencies
    4. If any downstream booking becomes infeasible, option is NOT feasible

    Returns (is_feasible, failure_reason, downstream_effects)
    """
    booking_map = {b.id: b.model_copy() for b in trip.bookings}

    # Replace the broken booking with the recovery option
    if replaced_booking_id not in booking_map:
        return False, "Booking to replace not found", []

    original = booking_map[replaced_booking_id]

    # Create a substitute booking from the recovery option
    substitute = original.model_copy()
    substitute.actual_departure = option.departure
    substitute.actual_arrival = option.arrival
    substitute.status = BookingStatus.CONFIRMED

    booking_map[replaced_booking_id] = substitute

    # Check downstream dependencies
    dep_map = {}
    for d in trip.dependencies:
        dep_map.setdefault(d.from_booking_id, []).append(d)

    downstream_effects: list[CascadeEffect] = []

    # Walk downstream from replaced booking
    to_check = [replaced_booking_id]
    checked = set()

    while to_check:
        current_id = to_check.pop(0)
        if current_id in checked:
            continue
        checked.add(current_id)

        current = booking_map[current_id]
        deps_from_current = dep_map.get(current_id, [])

        for dep in deps_from_current:
            successor = booking_map.get(dep.to_booking_id)
            if successor is None:
                continue

            slack = calculate_slack(current, successor, dep)

            if slack < 0:
                # Check if it's a non-transport booking
                if successor.type == BookingType.HOTEL:
                    # For hotels, check against late check-in cutoff
                    late_cutoff = successor.metadata.get("late_check_in_cutoff")
                    if late_cutoff:
                        cutoff_hour, cutoff_min = map(int, late_cutoff.split(":"))
                        arrival_with_transfer = (
                            get_effective_arrival(current)
                            + timedelta(minutes=dep.min_transfer_minutes)
                        )
                        cutoff_time = successor.scheduled_departure.replace(
                            hour=cutoff_hour, minute=cutoff_min,
                        )
                        if arrival_with_transfer > cutoff_time:
                            reason = (
                                f"NOT FEASIBLE: Arrival at {successor.destination} at "
                                f"{arrival_with_transfer.strftime('%H:%M')} exceeds "
                                f"hotel late check-in cutoff at {late_cutoff}."
                            )
                            downstream_effects.append(CascadeEffect(
                                booking_id=successor.id,
                                original_status=BookingStatus.CONFIRMED,
                                new_status=BookingStatus.INFEASIBLE,
                                slack_minutes=slack,
                                explanation=reason,
                                affected_by=current_id,
                            ))
                            return False, reason, downstream_effects
                        # Late check-in is allowed — mark as AT_RISK
                        downstream_effects.append(CascadeEffect(
                            booking_id=successor.id,
                            original_status=BookingStatus.CONFIRMED,
                            new_status=BookingStatus.AT_RISK,
                            slack_minutes=slack,
                            explanation=f"Hotel check-in late but within cutoff ({late_cutoff})",
                            affected_by=current_id,
                        ))
                    else:
                        reason = (
                            f"NOT FEASIBLE: Arrival + transfer exceeds "
                            f"{successor.reference} at {successor.destination}."
                        )
                        downstream_effects.append(CascadeEffect(
                            booking_id=successor.id,
                            original_status=BookingStatus.CONFIRMED,
                            new_status=BookingStatus.INFEASIBLE,
                            slack_minutes=slack,
                            explanation=reason,
                            affected_by=current_id,
                        ))
                        return False, reason, downstream_effects

                elif successor.type == BookingType.ATTRACTION:
                    reason = (
                        f"NOT FEASIBLE: Cannot reach {successor.reference} "
                        f"({successor.destination}) before entry window closes."
                    )
                    downstream_effects.append(CascadeEffect(
                        booking_id=successor.id,
                        original_status=BookingStatus.CONFIRMED,
                        new_status=BookingStatus.FORFEITED,
                        slack_minutes=slack,
                        explanation=reason,
                        affected_by=current_id,
                    ))
                    return False, reason, downstream_effects
                else:
                    reason = (
                        f"NOT FEASIBLE: Downstream {successor.reference} "
                        f"becomes infeasible (slack: {slack:.0f} min)."
                    )
                    downstream_effects.append(CascadeEffect(
                        booking_id=successor.id,
                        original_status=BookingStatus.CONFIRMED,
                        new_status=BookingStatus.INFEASIBLE,
                        slack_minutes=slack,
                        explanation=reason,
                        affected_by=current_id,
                    ))
                    return False, reason, downstream_effects
            elif slack < AT_RISK_THRESHOLD_MINUTES:
                downstream_effects.append(CascadeEffect(
                    booking_id=successor.id,
                    original_status=BookingStatus.CONFIRMED,
                    new_status=BookingStatus.AT_RISK,
                    slack_minutes=slack,
                    explanation=f"Tight connection: {slack:.0f} min slack.",
                    affected_by=current_id,
                ))

            # Update the successor for further downstream checks
            to_check.append(dep.to_booking_id)

    return True, None, downstream_effects


def score_option(
    option: RecoveryOption,
    original_booking: Booking,
    trip: Trip,
) -> dict[str, float]:
    """
    Score a recovery option using a transparent, deterministic formula.

    Components:
    - time_score: How much later the option arrives (lower is better)
    - cost_score: How much more expensive (lower is better)
    - disruption_score: How many downstream bookings are affected
    - feasibility_bonus: Bonus for being fully feasible
    """
    # Time score: minutes of delay compared to original arrival
    original_arrival = original_booking.scheduled_arrival
    option_arrival = option.arrival
    delay_minutes = (option_arrival - original_arrival).total_seconds() / 60.0
    # Normalize: 0 = same time, 1 = 6 hours later
    time_score = max(0, min(1, delay_minutes / 360.0))

    # Cost score: relative cost difference
    if option.price and original_booking.price:
        cost_ratio = option.price / original_booking.price
        cost_score = max(0, min(1, (cost_ratio - 0.5) / 1.5))
    else:
        cost_score = 0.5  # Unknown cost

    # Disruption score: based on downstream effects
    disruption_count = len(option.downstream_effects)
    disruption_score = min(1, disruption_count / 3.0)

    # Feasibility bonus
    feasibility_bonus = 0.0 if option.feasible else 1.0

    # Composite score (lower is better)
    total = (
        W_TIME * time_score
        + W_COST * cost_score
        + W_DISRUPTION * disruption_score
        + W_FEASIBILITY * feasibility_bonus
    )

    return {
        "total": round(total, 3),
        "time_score": round(time_score, 3),
        "cost_score": round(cost_score, 3),
        "disruption_score": round(disruption_score, 3),
        "feasibility_penalty": round(feasibility_bonus, 3),
        "delay_minutes": round(delay_minutes, 1),
    }


def evaluate_recovery_options(
    candidates: list[RecoveryOption],
    trip: Trip,
    replaced_booking_id: str,
) -> list[RecoveryOption]:
    """
    Evaluate all recovery candidates:
    1. Check feasibility of each
    2. Score each option
    3. Sort by score (feasible options first, then by score)

    Returns the evaluated and ranked list.
    """
    booking_map = {b.id: b for b in trip.bookings}
    original = booking_map.get(replaced_booking_id)
    if original is None:
        return candidates

    evaluated: list[RecoveryOption] = []

    for candidate in candidates:
        # Check feasibility
        feasible, failure_reason, downstream = check_recovery_feasibility(
            candidate, trip, replaced_booking_id,
        )

        # Update candidate
        candidate.feasible = feasible
        candidate.failure_reason = failure_reason
        candidate.downstream_effects = downstream

        # Score
        breakdown = score_option(candidate, original, trip)
        candidate.score = breakdown["total"]
        candidate.scoring_breakdown = breakdown

        evaluated.append(candidate)

    # Sort: feasible first, then by score (lower is better)
    evaluated.sort(key=lambda o: (not o.feasible, o.score))

    return evaluated
