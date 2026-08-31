# SANDHI — Problem Statement

## The Traveller's Real Problem

When a flight is delayed, most travellers focus on the delay itself. But the flight delay is rarely the real problem.

The real problem is **everything downstream**.

A 3-hour flight delay can silently trigger:

- A missed train connection
- A forfeited hotel booking past its free cancellation window
- A timed museum entry that becomes unusable
- A refund deadline that expires while the traveller is still stranded at the airport

**The delay is not an event. It is a set of countdowns nobody told you had started.**

## Why Existing Travel Tools Are Insufficient

### 1. Booking-Level Thinking

Existing travel platforms (MakeMyTrip, Goibibo, Google Flights, IRCTC) manage **individual bookings**. They do not understand how bookings relate to each other in time.

When a flight is delayed, the airline app may show the new departure time. But it has no knowledge of the train, hotel, or attraction booked separately.

### 2. No Dependency Awareness

A multi-modal itinerary — flight, then transfer, then train, then hotel — is a **chain of temporal dependencies**. If one link breaks, downstream links may become infeasible. No mainstream consumer tool models this dependency chain.

### 3. No Deadline Visibility

Travel bookings carry hidden deadlines:

- Railway TDR filing windows
- Hotel free-cancellation cutoffs
- Airline compensation claim windows (DGCA rules)
- Attraction no-show/refund policies

These deadlines are scattered across booking confirmations, terms of service, and government regulations. Travellers rarely know them, and never see them as **countdowns**.

### 4. No Policy Computation

Indian travel operates under specific regulatory frameworks:

- **DGCA Civil Aviation Requirements** for airline passenger rights
- **Indian Railway refund rules** for train cancellations
- **Consumer Protection Act** provisions
- Airline-specific Conditions of Carriage

Computing what a traveller is actually entitled to requires reading multiple policy documents, identifying applicable clauses, and performing date/time/amount calculations. No consumer tool does this automatically.

### 5. Cascading Consequences Are Invisible

When a disruption occurs, the traveller must manually:

1. Check each downstream booking
2. Look up each cancellation/refund policy
3. Calculate whether connections are still possible
4. Determine refund/rebooking deadlines
5. Decide which bookings to cancel, rebook, or claim against
6. Do all of this under time pressure, often while stranded

This is cognitively overwhelming and financially costly.

## The Indian Travel Ecosystem Context

India's travel ecosystem has specific characteristics that make this problem acute:

- **Multi-modal journeys are common**: Domestic flights + train connections + local transport is a standard pattern for millions of travellers.
- **Separate booking platforms**: Flights, trains, hotels, and attractions are typically booked on different platforms with no cross-platform awareness.
- **Complex regulatory landscape**: DGCA rules, Railway rules, and consumer protection laws provide real entitlements, but travellers rarely know or exercise them.
- **High volume**: India's domestic air traffic and railway traffic are among the highest in the world. Disruptions affect millions of journeys annually.
- **Price sensitivity**: The financial impact of a missed connection — lost tickets, rebooking costs, forfeited prepaid bookings — is proportionally significant for most Indian travellers.

## The Desired Outcome

A traveller whose itinerary is disrupted should immediately see:

1. **Which downstream bookings are affected** and why
2. **What deadlines are now ticking** — with live countdowns
3. **What they are entitled to** under applicable rules — with source references
4. **What recovery options exist** — verified against the actual remaining itinerary
5. **The source and provenance** behind every important number

The goal is to transform a chaotic, information-poor disruption experience into a structured, actionable decision space — in seconds, not hours.
