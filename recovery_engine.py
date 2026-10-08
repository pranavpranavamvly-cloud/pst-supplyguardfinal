"""
SupplyGuard AI — Recovery Decision Engine
Generates explainable, rule-based recovery options by analyzing route availability,
transit durations, stock cover runway, and alternative warehouse replenishment sources.

Transparent Multi-Criteria Decision Model:
- Considers route availability, estimated delivery time, destination stockout runway,
  and alternative warehouse stock levels.
- Evaluates feasible mitigation options (Rerouting, Inter-hub Stock Transfer, Passive Monitoring, Escalation).
- Applies the user's recovery priority:
  * "Meet deadline first" (Prioritizes minimum time to prevent stockout)
  * "Minimize cost" (Prioritizes lowest operational and transfer expense)
  * "Balance cost and time" (Balanced weighted optimization)
"""

from typing import Dict, List, Optional, Any, Union
import math


def evaluate_transfer_candidate(
    source: Dict[str, Any],
    destination: str,
    roads: Dict[Any, Dict[str, Any]],
    demand_per_hour: float,
    needed_hours: float,
    transfer_cost_per_unit: float
) -> Optional[Dict[str, Any]]:
    """
    Evaluates transferring stock from an alternative warehouse to the destination.
    Calculates transfer time, transfer units, and costs based on the road network.
    """
    source_wh = source.get("Warehouse")
    available_stock = float(source.get("Available stock", 0))

    if available_stock <= 0:
        return None

    # Estimate transit time & distance from source warehouse to destination
    # Check direct link first
    transit_time = None
    transit_km = None
    for (u, v), edge in roads.items():
        if edge.get("open", True) and set([u, v]) == set([source_wh, destination]):
            transit_time = float(edge["hours"])
            transit_km = float(edge["km"])
            break

    # If no direct edge, use fallback estimates based on network topology
    if transit_time is None:
        if source_wh == "North Hub":
            transit_time = 0.50
            transit_km = 12.0
        elif source_wh == "East Hub":
            transit_time = 0.40
            transit_km = 9.0
        elif source_wh == "Central Warehouse":
            transit_time = 1.30
            transit_km = 38.0
        else:
            transit_time = 1.0
            transit_km = 25.0

    # Determine recommended units to transfer (bridge buffer until full shipment arrives)
    burn_rate = max(1.0, float(demand_per_hour))
    recommended_units = min(available_stock, max(10, math.ceil(burn_rate * max(needed_hours, 4.0))))

    # Transfer cost calculation:
    # Handling/packaging fee + per-unit freight + vehicle fuel/dispatch base
    transit_freight = round(transit_km * 1.25, 2)
    inventory_handling = round(recommended_units * transfer_cost_per_unit, 2)
    dispatch_fee = 20.0
    total_cost = round(transit_freight + inventory_handling + dispatch_fee, 2)

    return {
        "source_warehouse": source_wh,
        "available_stock": int(available_stock),
        "transfer_units": int(recommended_units),
        "transit_time_hours": transit_time,
        "transit_distance_km": transit_km,
        "total_cost_usd": total_cost,
        "inventory_cost": inventory_handling,
        "freight_cost": transit_freight + dispatch_fee
    }


def generate_all_options(
    route: List[str],
    route_hours: Optional[float],
    route_km: Optional[float],
    stockout_hours: float,
    destination_stock: float,
    demand_per_hour: float,
    sources: List[Dict[str, Any]],
    roads: Optional[Dict[Any, Dict[str, Any]]] = None,
    priority: str = "Balance cost and time",
    transfer_cost_per_unit: float = 0.8
) -> List[Dict[str, Any]]:
    """
    Evaluates and generates all candidate recovery actions with explainable metrics.
    """
    options = []
    has_route = bool(route) and route_hours is not None
    is_immediate_stockout_risk = (not math.isinf(stockout_hours)) and (stockout_hours < (route_hours or 0.0))
    effective_roads = roads or {}

    # Option 1: Maintain Active Route (Standard Reroute / Primary Path)
    if has_route:
        base_freight_cost = round((route_km or 30.0) * 1.50 + 40.0, 2)
        stockout_penalty = 0.0
        if is_immediate_stockout_risk:
            deficit_h = round((route_hours or 0.0) - stockout_hours, 2)
            stockout_penalty = round(deficit_h * 50.0, 2)

        options.append({
            "id": "OPT-REROUTE",
            "title": f"Dispatch via Computed Route ({' → '.join(route)})",
            "category": "REROUTE",
            "action": f"Dispatch shipment via optimal corridor: {' → '.join(route)}",
            "estimated_time_hours": round(route_hours, 2),
            "estimated_cost_usd": base_freight_cost,
            "stockout_prevented": not is_immediate_stockout_risk,
            "feasibility": "FEASIBLE",
            "reason": (
                f"Active route exists ({route_hours:.2f} hrs, {route_km:.1f} km). "
                + (f"However, stock runs out in {stockout_hours:.1f} hrs, leaving a {round(route_hours - stockout_hours, 1)}h stockout gap."
                   if is_immediate_stockout_risk else
                   f"Stock cover ({stockout_hours:.1f} hrs) safely exceeds delivery time.")
            ),
            "risks_and_assumptions": (
                "Destination will face a stockout before arrival unless supplemented with an expedited transfer."
                if is_immediate_stockout_risk else
                "Assumes no sudden downstream blockages or traffic surges along the transit corridor."
            ),
            "cost_breakdown": f"Freight: ${base_freight_cost:.2f}" + (f" + Stockout Delay Risk: ${stockout_penalty:.2f}" if stockout_penalty > 0 else "")
        })

    # Option 2 & 3: Stock Transfers from Alternative Warehouses
    for src in sources:
        cand = evaluate_transfer_candidate(
            source=src,
            destination="Hospital",
            roads=effective_roads,
            demand_per_hour=demand_per_hour,
            needed_hours=route_hours or 4.0,
            transfer_cost_per_unit=transfer_cost_per_unit
        )
        if cand:
            can_prevent = (stockout_hours >= cand["transit_time_hours"]) or (cand["transit_time_hours"] < (route_hours or 99.0))
            comp_text = f"{route_hours:.2f} hrs for main shipment" if route_hours is not None else "primary corridor blocked"
            options.append({
                "id": f"OPT-XFER-{cand['source_warehouse'].replace(' ', '_').upper()}",
                "title": f"Emergency Transfer from {cand['source_warehouse']}",
                "category": "TRANSFER",
                "action": f"Deploy hot-shot transfer of {cand['transfer_units']} units from {cand['source_warehouse']}",
                "estimated_time_hours": round(cand["transit_time_hours"], 2),
                "estimated_cost_usd": round(cand["total_cost_usd"], 2),
                "stockout_prevented": can_prevent,
                "feasibility": "FEASIBLE",
                "reason": (
                    f"{cand['source_warehouse']} has {cand['available_stock']} units available. "
                    f"Rapid transfer arrives in {cand['transit_time_hours']:.2f} hrs (vs {comp_text}). "
                    f"Provides {cand['transfer_units']} units to safeguard local operations."
                ),
                "risks_and_assumptions": (
                    f"Consumes stock at {cand['source_warehouse']} (leaves {cand['available_stock'] - cand['transfer_units']} units). "
                    "Requires dedicated local hot-shot courier vehicle."
                ),
                "cost_breakdown": f"Inventory handling: ${cand['inventory_cost']:.2f} + Expedited freight: ${cand['freight_cost']:.2f}"
            })

    # Option 4: Passive Monitoring (Only appropriate when risk is low)
    if has_route and not is_immediate_stockout_risk:
        options.append({
            "id": "OPT-MONITOR",
            "title": "Maintain Baseline Monitoring",
            "category": "MONITOR",
            "action": "Maintain active telemetry monitoring without initiating emergency interventions",
            "estimated_time_hours": round(route_hours, 2),
            "estimated_cost_usd": 0.0,
            "stockout_prevented": True,
            "feasibility": "FEASIBLE",
            "reason": (
                f"Destination stock cover ({stockout_hours:.1f} hrs) provides an ample buffer "
                f"over expected delivery time ({route_hours:.2f} hrs). Operational risk is low."
            ),
            "risks_and_assumptions": (
                "Continuous monitoring only; will alert if transit delay exceeds 1.5 hours."
            ),
            "cost_breakdown": "$0.00 (Standard operation)"
        })

    # Option 5: Emergency Escalation (When no route or zero inventory available)
    if not has_route and not sources:
        options.append({
            "id": "OPT-ESCALATE",
            "title": "Emergency Cross-Network Procurement Escalation",
            "category": "ESCALATE",
            "action": "Trigger emergency air-lift or external supplier spot-market acquisition",
            "estimated_time_hours": 6.0,
            "estimated_cost_usd": 500.0,
            "stockout_prevented": False,
            "feasibility": "LAST_RESORT",
            "reason": "Both delivery road network and regional hub inventories are completely depleted or cut off.",
            "risks_and_assumptions": "High spot-market procurement premium; unconfirmed vendor response SLA.",
            "cost_breakdown": "Estimated premium emergency dispatch & procurement contract."
        })

    # Scoring & Prioritization
    for opt in options:
        t = opt["estimated_time_hours"] or 99.0
        c = opt["estimated_cost_usd"] or 999.0
        prevents = 1.0 if opt["stockout_prevented"] else 0.2

        if priority == "Meet deadline first":
            # 70% time, 20% stockout prevention, 10% cost
            score = (100.0 / (1.0 + t * 2.0)) * 0.70 + (prevents * 50.0) * 0.20 + (100.0 / (1.0 + c * 0.01)) * 0.10
        elif priority == "Minimize cost":
            # 60% cost, 25% stockout prevention, 15% time
            score = (100.0 / (1.0 + c * 0.02)) * 0.60 + (prevents * 50.0) * 0.25 + (100.0 / (1.0 + t * 1.5)) * 0.15
        else:  # "Balance cost and time"
            # 40% time, 30% cost, 30% stockout prevention
            score = (100.0 / (1.0 + t * 1.8)) * 0.40 + (100.0 / (1.0 + c * 0.015)) * 0.30 + (prevents * 50.0) * 0.30

        opt["score"] = round(score, 1)

    # Sort options by score descending
    options.sort(key=lambda x: x["score"], reverse=True)
    if options:
        options[0]["is_recommended"] = True
        for o in options[1:]:
            o["is_recommended"] = False

    return options


def recommend_recovery(
    route: List[str],
    route_hours: Optional[float],
    route_km: Optional[float],
    stockout_hours: float,
    sources: List[Dict[str, Any]],
    priority: str = "Balance cost and time",
    transfer_cost_per_unit: float = 0.8,
    destination_stock: float = 12.0,
    demand_per_hour: float = 8.0,
    roads: Optional[Dict[Any, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Main entry point for recovery recommendations.
    Maintains full backward compatibility with the original signature while providing
    rich explainability, multi-option trade-off evaluations, and exact metrics.
    """
    route_exists = bool(route) and route_hours is not None
    urgent_stock = (not math.isinf(stockout_hours)) and (stockout_hours <= 4.0)
    stockout_before_delivery = route_exists and (not math.isinf(stockout_hours)) and (route_hours > stockout_hours)
    
    # Generate all candidate options
    all_options = generate_all_options(
        route=route,
        route_hours=route_hours,
        route_km=route_km,
        stockout_hours=stockout_hours,
        destination_stock=destination_stock,
        demand_per_hour=demand_per_hour,
        sources=sources,
        roads=roads,
        priority=priority,
        transfer_cost_per_unit=transfer_cost_per_unit
    )

    explanations: List[str] = []

    # Determine Urgency & Strategy
    if not route_exists:
        urgency = "CRITICAL"
        headline = "CRITICAL: Primary delivery route is completely blocked."
        if sources:
            best_source = sources[0]["Warehouse"]
            action = f"Execute emergency transfer from {best_source}"
            reason = (
                f"All direct transport corridors from origin to destination are impassable. "
                f"Emergency stock transfer from {best_source} is recommended to prevent immediate operational failure."
            )
        else:
            action = "Escalate critical supply failure & source external inventory"
            headline = "CRITICAL: Complete network severance with zero replenishment sources."
            reason = "No open road corridor exists and no alternative regional warehouse contains available stock."

    elif stockout_before_delivery:
        deficit = round(route_hours - stockout_hours, 1)
        urgency = "CRITICAL"
        headline = f"CRITICAL: Destination stock will exhaust {deficit} hours before delivery arrives."
        if sources and priority != "Minimize cost":
            best_source = sources[0]["Warehouse"]
            action = f"Hot-shot transfer from {best_source} + Reroute primary shipment"
            reason = (
                f"Delivery ETA ({route_hours:.2f} hrs) exceeds destination stock cover ({stockout_hours:.1f} hrs). "
                f"An expedited hot-shot transfer from {best_source} arrives faster to bridge the {deficit}-hour deficit."
            )
        elif sources:
            best_source = sources[0]["Warehouse"]
            action = f"Low-cost transfer from {best_source}"
            reason = (
                f"Stock deficit detected. Transfer from {best_source} recommended under '{priority}' "
                "to minimize operational penalties while ensuring continuity."
            )
        else:
            action = "Expedite primary carrier transit & issue rationing notice"
            reason = f"No alternative warehouse has inventory. Accelerate primary carrier on fastest open path."

    elif urgent_stock:
        urgency = "HIGH"
        headline = f"HIGH RISK: Destination stock cover is critical ({stockout_hours:.1f} hrs remaining)."
        if route_exists:
            action = f"Prioritize transit along optimal route: {' → '.join(route)}"
            reason = (
                f"Current stock cover ({stockout_hours:.1f} hrs) is within the safety threshold. "
                f"Estimated delivery time is {route_hours:.2f} hrs. Route priority dispatch advised."
            )
        else:
            action = "Initiate emergency replenishment"
            reason = "Destination inventory is near exhaustion."

    elif route_exists and route != ["Central Warehouse", "Hospital"] and any(not e.get("open", True) or "Congestion" in e.get("condition", "") for e in (roads or {}).values()):
        # Route was rerouted via alternative corridor due to network disruption
        urgency = "MEDIUM"
        headline = f"ADVISORY: Shipment rerouted via alternative corridor: {' -> '.join(route)}"
        action = f"Maintain rerouted transit via {route[1] if len(route) > 2 else route[0]}"
        reason = f"Dijkstra optimizer identified {' → '.join(route)} as the fastest open path ({route_hours:.2f} hrs, {route_km:.1f} km)."

    else:
        urgency = "LOW"
        headline = "NORMAL: Operations stable within safety parameters."
        action = "Maintain regular dispatch and monitor network telemetry"
        reason = (
            f"Road network is open ({route_hours:.2f} hrs). Destination inventory cover "
            f"({stockout_hours:.1f} hrs) safely exceeds delivery window."
        )

    # Compile explainable reasoning bullets
    if route_exists:
        explanations.append(f"Optimal Dijkstra path: {' → '.join(route)} ({route_hours:.2f} hrs, {route_km:.1f} km).")
    else:
        explanations.append("Dijkstra path search returned no feasible route; all modeled edges to destination are blocked.")

    if math.isinf(stockout_hours):
        explanations.append("Destination stock cover is Infinite (zero hourly consumption).")
    else:
        explanations.append(
            f"Destination stock cover: {stockout_hours:.1f} hrs (Current stock: {destination_stock:.0f} units, Demand: {demand_per_hour:.1f}/hr)."
        )

    explanations.append(f"Recovery priority objective: '{priority}'.")
    explanations.append(f"Candidate warehouses evaluated: {len(sources)} available with positive inventory.")
    explanations.append("Decision logic uses transparent deterministic rules with verifiable formulas, not opaque ML.")

    # Determine recommended option object
    best_opt = next((o for o in all_options if o.get("is_recommended")), all_options[0] if all_options else None)

    return {
        "urgency": urgency,
        "headline": headline,
        "reason": reason,
        "action": action,
        "explanations": explanations,
        "options": all_options,
        "best_option": best_opt,
        "stockout_before_delivery": stockout_before_delivery,
        "estimated_recovery_cost": best_opt.get("estimated_cost_usd", 0.0) if best_opt else 0.0,
    }
