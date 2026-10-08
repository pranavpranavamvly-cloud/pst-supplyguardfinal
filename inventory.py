"""
SupplyGuard AI — Inventory Risk Analysis & Replenishment Modeling
Provides reliable inventory calculations, stock-cover projections, delivery buffer
comparisons, and safety-stock evaluations.
Supports both pandas DataFrames and native dictionary records.
"""

import math
from typing import Dict, List, Optional, Any, Union

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def _is_missing(val: Any) -> bool:
    """Safe check for None, NaN, or missing values without strict dependency on pandas."""
    if val is None:
        return True
    if HAS_PANDAS and pd.isna(val):
        return True
    try:
        return math.isnan(float(val))
    except (ValueError, TypeError):
        return False


def stockout_hours(stock: Union[float, int, None], demand_per_hour: Union[float, int, None]) -> float:
    """
    Estimate hours until stockout: Stock cover (hours) = Available stock / Hourly demand.
    Safely handles zero demand, negative values, and None/NaN.
    
    Returns:
        float: Number of hours until exhaustion, or float('inf') if demand is zero/negative.
    """
    if _is_missing(stock):
        return 0.0
    if _is_missing(demand_per_hour):
        return float("inf")

    try:
        stock_val = max(0.0, float(stock))
        demand_val = float(demand_per_hour)
    except (ValueError, TypeError):
        return 0.0

    if demand_val <= 0:
        return float("inf")

    return stock_val / demand_val


def format_stock_cover(hours: float) -> str:
    """Format stock cover hours into an operator-friendly string."""
    if math.isinf(hours):
        return "∞ (Zero demand)"
    if hours <= 0:
        return "0.0 hrs (Exhausted)"
    if hours < 1.0:
        return f"{hours * 60:.0f} mins"
    return f"{hours:.1f} hrs"


def assess_inventory_risk(
    stock: Union[float, int],
    demand_per_hour: Union[float, int],
    eta_hours: Optional[float] = None
) -> Dict[str, Any]:
    """
    Comprehensive risk analysis comparing stock cover against shipment arrival time.
    Provides transparent calculations and explicit explanations.
    """
    cover = stockout_hours(stock, demand_per_hour)
    stock_val = max(0.0, float(stock) if not _is_missing(stock) else 0.0)
    demand_val = max(0.0, float(demand_per_hour) if not _is_missing(demand_per_hour) else 0.0)

    # Base conditions
    if stock_val == 0:
        urgency = "CRITICAL"
        status = "Immediate Stockout"
        badge_color = "#EF4444"
        explanation = (
            f"Zero units in stock at destination with an active burn rate of {demand_val:.1f} units/hr. "
            "Facility is currently facing an active stockout."
        )
        buffer_hours = -eta_hours if eta_hours is not None else -999.0

    elif math.isinf(cover):
        urgency = "LOW"
        status = "No Depletion"
        badge_color = "#10B981"
        explanation = f"Current stock is {stock_val:.0f} units with zero hourly demand. Inventory is stable."
        buffer_hours = float("inf")

    elif eta_hours is None:
        # No delivery route or pending shipment
        if cover < 2.0:
            urgency = "CRITICAL"
            status = "Critical Shortage (<2h)"
            badge_color = "#EF4444"
            explanation = f"Critical stock cover ({cover:.1f} hrs) with no confirmed delivery route active."
        elif cover < 6.0:
            urgency = "HIGH"
            status = "Low Stock Warning"
            badge_color = "#F59E0B"
            explanation = f"Low stock cover ({cover:.1f} hrs remaining) without inbound transit link."
        else:
            urgency = "LOW"
            status = "Stable Inventory"
            badge_color = "#10B981"
            explanation = f"Adequate stock cover ({cover:.1f} hrs remaining) under current demand."
        buffer_hours = None

    else:
        # Both stock cover and delivery ETA are available
        buffer_hours = cover - eta_hours
        if buffer_hours < 0:
            urgency = "CRITICAL"
            status = "Stockout Before Delivery"
            badge_color = "#EF4444"
            deficit = abs(buffer_hours)
            explanation = (
                f"DEFICIT DETECTED: Stock will be exhausted in {cover:.1f} hrs, but shipment arrives in "
                f"{eta_hours:.1f} hrs. Facility will face a {deficit:.1f}-hour stockout window before replenishment."
            )
        elif buffer_hours < 2.0:
            urgency = "HIGH"
            status = "High Delay Sensitivity"
            badge_color = "#F59E0B"
            explanation = (
                f"TIGHT MARGIN: Stock cover is {cover:.1f} hrs and shipment ETA is {eta_hours:.1f} hrs. "
                f"Safety buffer is only {buffer_hours:.1f} hrs. Any transit delay risks stockout."
            )
        else:
            urgency = "LOW"
            status = "Replenishment Secure"
            badge_color = "#10B981"
            explanation = (
                f"HEALTHY BUFFER: Stock cover ({cover:.1f} hrs) safely exceeds shipment arrival ({eta_hours:.1f} hrs) "
                f"with a {buffer_hours:.1f}-hour safety buffer."
            )

    return {
        "stock": stock_val,
        "demand_per_hour": demand_val,
        "cover_hours": cover,
        "eta_hours": eta_hours,
        "buffer_hours": buffer_hours,
        "status": status,
        "urgency": urgency,
        "badge_color": badge_color,
        "explanation": explanation,
        "calculation_formula": f"Stock Cover ({format_stock_cover(cover)}) = Stock ({stock_val:.0f}) ÷ Demand ({demand_val:.1f}/hr)"
    }


def find_replenishment_sources(
    inventory: Any,
    product: str,
    exclude: Optional[str] = None,
    required_units: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Search across distribution network for candidate replenishment warehouses.
    Accepts pandas DataFrame or list of dicts.
    Validates available stock and checks whether warehouse can fulfill required quantity.
    """
    if inventory is None:
        return []

    # Normalize input into list of dicts
    records = []
    if HAS_PANDAS and isinstance(inventory, pd.DataFrame):
        if inventory.empty:
            return []
        records = inventory.to_dict(orient="records")
    elif isinstance(inventory, list):
        records = inventory
    else:
        return []

    # Clean filtering
    sources = []
    target_product = product.strip().lower()
    exclude_wh = str(exclude).strip().lower() if exclude else None

    for row in records:
        wh = str(row.get("Warehouse", "")).strip()
        prod = str(row.get("Product", "")).strip().lower()
        if prod != target_product:
            continue
        if exclude_wh and wh.lower() == exclude_wh:
            continue

        try:
            stock = float(row.get("Stock", 0))
            daily_d = float(row.get("Daily demand", 0))
        except (ValueError, TypeError):
            continue

        if stock <= 0:
            continue

        local_cover = stockout_hours(stock, daily_d / 24.0)
        own_reserve = (daily_d / 24.0) * 12.0
        transferable = max(0.0, stock - own_reserve)

        has_sufficient = True
        if required_units is not None and required_units > 0:
            has_sufficient = stock >= required_units

        sources.append({
            "Warehouse": wh,
            "Available stock": int(stock),
            "Daily demand": int(daily_d),
            "Local cover (hours)": round(local_cover, 1) if not math.isinf(local_cover) else 999.0,
            "Transferable surplus": int(transferable),
            "Can fulfill demand": has_sufficient
        })

    sources.sort(key=lambda s: s["Available stock"], reverse=True)
    return sources
