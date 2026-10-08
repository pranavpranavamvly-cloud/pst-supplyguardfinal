"""
SupplyGuard AI — Logistics Crisis Control Tower & Recovery Platform
A professional supply-chain crisis monitoring, route optimization, and explainable recovery dashboard.
"""

import math
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Internal modules
from route_optimizer import (
    build_network,
    shortest_path,
    find_alternative_paths,
    get_edge_details,
    NODE_METADATA,
    DEFAULT_ROADS
)
from inventory import (
    stockout_hours,
    format_stock_cover,
    assess_inventory_risk,
    find_replenishment_sources
)
from recovery_engine import recommend_recovery, generate_all_options


# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & THEME STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SupplyGuard AI — Logistics Crisis Control Tower",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium dark navy & neon cyan control tower styling
st.markdown("""
<style>
    /* Global Background & Typography */
    .stApp {
        background-color: #0A0F1D;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Main container padding */
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 98%;
    }

    /* Custom Header Banner */
    .brand-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    }
    .brand-title {
        font-size: 1.65rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #F8FAFC;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .brand-subtitle {
        color: #94A3B8;
        font-size: 0.88rem;
        margin-top: 4px;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .badge-live {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-sim {
        background: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }

    /* Metric Cards */
    .sg-metric-card {
        background: #111A2E;
        border: 1px solid rgba(56, 189, 248, 0.16);
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        height: 100%;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .sg-metric-card:hover {
        border-color: rgba(56, 189, 248, 0.4);
    }
    .sg-metric-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #94A3B8;
        margin-bottom: 6px;
        font-weight: 600;
    }
    .sg-metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.2;
    }
    .sg-metric-delta {
        font-size: 0.8rem;
        margin-top: 5px;
        font-weight: 500;
    }
    .delta-positive { color: #34D399; }
    .delta-negative { color: #F87171; }
    .delta-neutral { color: #94A3B8; }

    /* Alert / Strategy Callouts */
    .strategy-card {
        background: #131E35;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        border-left: 5px solid #38BDF8;
    }
    .strategy-card.critical {
        border-left-color: #EF4444;
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-left-width: 6px;
    }
    .strategy-card.high {
        border-left-color: #F59E0B;
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-left-width: 6px;
    }
    .strategy-card.low {
        border-left-color: #10B981;
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-left-width: 6px;
    }

    /* Comparison Table Highlighting */
    .comp-box {
        background: #111A2E;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }

    /* Sidebar aesthetics */
    [data-testid="stSidebar"] {
        background-color: #0A0F1D;
        border-right: 1px solid rgba(56, 189, 248, 0.12);
    }
    
    /* Table & tab styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 6px 6px 0 0;
        color: #94A3B8;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.1) !important;
        color: #38BDF8 !important;
        border-bottom: 2px solid #38BDF8 !important;
    }

    /* Streamlit Metric Overrides */
    div[data-testid="stMetricValue"] {
        font-size: 1.55rem;
        color: #F8FAFC;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. SESSION STATE INITIALIZATION & LOGGING
# -----------------------------------------------------------------------------
def log_event(event_type: str, component: str, details: str, status: str = "INFO"):
    """Append a simulated event to the chronological event log."""
    if "event_log" not in st.session_state:
        st.session_state.event_log = []
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.event_log.append({
        "Timestamp": timestamp,
        "Event Type": event_type,
        "Component": component,
        "Details": details,
        "Status": status
    })


def reset_to_baseline():
    """Reset simulation state back to normal operating conditions."""
    st.session_state.scenario = "Normal operations"
    st.session_state.stock_at_destination = 12
    st.session_state.demand_per_hour = 8
    st.session_state.recovery_priority = "Balance cost and time"
    st.session_state.transfer_cost_per_unit = 0.8
    st.session_state.roads = {k: v.copy() for k, v in DEFAULT_ROADS.items()}
    st.session_state.simulation_count = st.session_state.get("simulation_count", 0) + 1
    log_event("RESET_BASELINE", "Simulator", "All system parameters reset to normal baseline conditions.", "NORMAL")


# Initialize session state variables
if "roads" not in st.session_state:
    st.session_state.roads = {k: v.copy() for k, v in DEFAULT_ROADS.items()}
if "scenario" not in st.session_state:
    st.session_state.scenario = "Normal operations"
if "stock_at_destination" not in st.session_state:
    st.session_state.stock_at_destination = 12
if "demand_per_hour" not in st.session_state:
    st.session_state.demand_per_hour = 8
if "recovery_priority" not in st.session_state:
    st.session_state.recovery_priority = "Balance cost and time"
if "transfer_cost_per_unit" not in st.session_state:
    st.session_state.transfer_cost_per_unit = 0.8
if "event_log" not in st.session_state:
    st.session_state.event_log = []
    log_event("SYSTEM_BOOT", "Control Tower", "SupplyGuard AI telemetry initialized successfully.", "OK")


# -----------------------------------------------------------------------------
# 3. DATA LOADING (SHIPMENTS & INVENTORY)
# -----------------------------------------------------------------------------
@st.cache_data
def load_shipments_data() -> pd.DataFrame:
    """Load shipment telemetry from CSV or initialize canonical simulated dataset."""
    try:
        df = pd.read_csv("data/sample_shipments.csv")
        # Ensure column normalization
        if "ETA_hours" in df.columns and "ETA (hours)" not in df.columns:
            df["ETA (hours)"] = df["ETA_hours"]
        return df
    except Exception:
        return pd.DataFrame([
            {"Shipment": "SG-101", "Product": "Emergency medicine", "Origin": "Central Warehouse", "Destination": "Hospital", "Status": "At risk", "ETA (hours)": 7.0, "Priority": "Critical"},
            {"Shipment": "SG-102", "Product": "Surgical kits", "Origin": "Central Warehouse", "Destination": "North Hub", "Status": "On time", "ETA (hours)": 1.0, "Priority": "High"},
            {"Shipment": "SG-103", "Product": "Food supplies", "Origin": "East Hub", "Destination": "Hospital", "Status": "Delayed", "ETA (hours)": 3.5, "Priority": "Medium"},
            {"Shipment": "SG-104", "Product": "Water filters", "Origin": "Central Warehouse", "Destination": "East Hub", "Status": "On time", "ETA (hours)": 0.8, "Priority": "Low"},
        ])


@st.cache_data
def load_base_inventory() -> pd.DataFrame:
    """Canonical network inventory across distribution hubs."""
    return pd.DataFrame([
        {"Warehouse": "Central Warehouse", "Product": "Emergency medicine", "Stock": 120, "Daily demand": 180},
        {"Warehouse": "North Hub", "Product": "Emergency medicine", "Stock": 80, "Daily demand": 96},
        {"Warehouse": "East Hub", "Product": "Emergency medicine", "Stock": 240, "Daily demand": 120},
        {"Warehouse": "Central Warehouse", "Product": "Surgical kits", "Stock": 60, "Daily demand": 30},
        {"Warehouse": "North Hub", "Product": "Surgical kits", "Stock": 18, "Daily demand": 24},
    ])


raw_shipments = load_shipments_data()
base_inventory = load_base_inventory()


# -----------------------------------------------------------------------------
# 4. SIDEBAR: CRISIS SIMULATOR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.markdown("""
<div style="padding: 10px 0 16px 0;">
    <div style="font-size: 1.15rem; font-weight: 700; color: #38BDF8; display: flex; align-items: center; gap: 8px;">
        ⚠️ Crisis Simulator
    </div>
    <div style="font-size: 0.8rem; color: #94A3B8;">Simulate and mitigate supply-chain disruptions in real time.</div>
</div>
""", unsafe_allow_html=True)

# Scenario selection
scenario_options = ["Normal operations", "Main route blocked", "Heavy traffic", "Demand spike"]
selected_scenario = st.sidebar.selectbox(
    "Disruption Scenario",
    scenario_options,
    index=scenario_options.index(st.session_state.scenario) if st.session_state.scenario in scenario_options else 0,
    help="Select an automated disruption event to model its systemic impact on routing and inventory."
)

st.sidebar.markdown("---")
st.sidebar.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #CBD5E1; margin-bottom: 6px;'>DESTINATION TELEMETRY</div>", unsafe_allow_html=True)

slider_stock = st.sidebar.slider(
    "Destination stock (units)",
    min_value=0,
    max_value=100,
    value=st.session_state.stock_at_destination,
    step=1,
    help="Current on-hand inventory at Hospital destination."
)

slider_demand = st.sidebar.slider(
    "Destination demand (units/hour)",
    min_value=0,
    max_value=30,
    value=st.session_state.demand_per_hour,
    step=1,
    help="Current consumption burn rate at Hospital destination."
)

st.sidebar.markdown("---")
st.sidebar.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #CBD5E1; margin-bottom: 6px;'>RECOVERY STRATEGY TUNING</div>", unsafe_allow_html=True)

priority_options = ["Balance cost and time", "Meet deadline first", "Minimize cost"]
selected_priority = st.sidebar.selectbox(
    "Recovery Priority Objective",
    priority_options,
    index=priority_options.index(st.session_state.recovery_priority) if st.session_state.recovery_priority in priority_options else 0,
    help="Guides the recovery engine's multi-criteria scoring algorithm."
)

input_transfer_cost = st.sidebar.number_input(
    "Transfer cost per unit ($)",
    min_value=0.0,
    max_value=10.0,
    value=float(st.session_state.transfer_cost_per_unit),
    step=0.1,
    help="Unit handling and transfer charge applied to inter-hub stock reallocations."
)

col_sim_btn, col_rst_btn = st.sidebar.columns(2)
simulate_clicked = col_sim_btn.button("🚨 Simulate Crisis", use_container_width=True, type="primary")
reset_clicked = col_rst_btn.button("↺ Reset Baseline", use_container_width=True)

if reset_clicked:
    reset_to_baseline()
    st.rerun()

if simulate_clicked:
    st.session_state.scenario = selected_scenario
    st.session_state.stock_at_destination = slider_stock
    st.session_state.demand_per_hour = slider_demand
    st.session_state.recovery_priority = selected_priority
    st.session_state.transfer_cost_per_unit = input_transfer_cost
    log_event("SCENARIO_SIMULATED", "Simulator", f"Scenario '{selected_scenario}' executed with stock={slider_stock}, demand={slider_demand}.", "WARNING")
    st.rerun()

# Update session state with current sidebar values if user adjusted sliders without clicking button
st.session_state.scenario = selected_scenario
st.session_state.stock_at_destination = slider_stock
st.session_state.demand_per_hour = slider_demand
st.session_state.recovery_priority = selected_priority
st.session_state.transfer_cost_per_unit = input_transfer_cost

# Advanced Network Disruption Expander in Sidebar
with st.sidebar.expander("🛠️ Advanced Edge Override (Manual)", expanded=False):
    st.caption("Manually toggle road segments to model custom compound disruptions:")
    manual_block_main = st.checkbox("Block Central ↔ Hospital", value=not st.session_state.roads[("Central Warehouse", "Hospital")].get("open", True))
    manual_block_north = st.checkbox("Block North Hub ↔ Hospital", value=not st.session_state.roads[("North Hub", "Hospital")].get("open", True))
    manual_block_east = st.checkbox("Block East Hub ↔ Hospital", value=not st.session_state.roads[("East Hub", "Hospital")].get("open", True))


# -----------------------------------------------------------------------------
# 5. CORE COMPUTATION: BASELINE & ACTIVE SCENARIO EVALUATION
# -----------------------------------------------------------------------------
# Compute baseline state (Normal operations with default stock=12, demand=8)
baseline_roads = {k: v.copy() for k, v in DEFAULT_ROADS.items()}
baseline_network = build_network(baseline_roads)
base_route, base_route_hours, base_route_km = shortest_path(baseline_network, "Central Warehouse", "Hospital", weight="hours")
base_stock_cover = stockout_hours(12, 8)
base_risk = assess_inventory_risk(12, 8, eta_hours=base_route_hours)
base_cost = round((base_route_km or 30.0) * 1.50 + 40.0, 2) if base_route_km else 85.0

# Build active disrupted roads dictionary
active_roads = {k: v.copy() for k, v in DEFAULT_ROADS.items()}
active_demand = float(st.session_state.demand_per_hour)
active_stock = float(st.session_state.stock_at_destination)

# Apply scenario-specific disruptions
if st.session_state.scenario == "Main route blocked":
    active_roads[("Central Warehouse", "Hospital")]["open"] = False
    active_roads[("Central Warehouse", "Hospital")]["condition"] = "Blocked"
elif st.session_state.scenario == "Heavy traffic":
    active_roads[("Central Warehouse", "Hospital")]["hours"] = round(DEFAULT_ROADS[("Central Warehouse", "Hospital")]["hours"] * 2.6, 2)
    active_roads[("Central Warehouse", "Hospital")]["condition"] = "Heavy Congestion (2.6x delay)"
    active_roads[("North Hub", "Hospital")]["hours"] = round(DEFAULT_ROADS[("North Hub", "Hospital")]["hours"] * 1.8, 2)
    active_roads[("North Hub", "Hospital")]["condition"] = "Moderate Congestion (1.8x delay)"
elif st.session_state.scenario == "Demand spike":
    # Demand spikes by 70%
    active_demand = int(round(active_demand * 1.7))

# Apply manual override checkboxes if toggled
if manual_block_main:
    active_roads[("Central Warehouse", "Hospital")]["open"] = False
    active_roads[("Central Warehouse", "Hospital")]["condition"] = "Blocked (Manual)"
if manual_block_north:
    active_roads[("North Hub", "Hospital")]["open"] = False
    active_roads[("North Hub", "Hospital")]["condition"] = "Blocked (Manual)"
if manual_block_east:
    active_roads[("East Hub", "Hospital")]["open"] = False
    active_roads[("East Hub", "Hospital")]["condition"] = "Blocked (Manual)"

# Run Dijkstra on active network
active_network = build_network(active_roads)
active_route, active_route_hours, active_route_km = shortest_path(active_network, "Central Warehouse", "Hospital", weight="hours")

# Alternative paths discovery
alternative_routes = find_alternative_paths(active_roads, "Central Warehouse", "Hospital", active_route)

# Inventory risk evaluation for destination
active_stock_cover = stockout_hours(active_stock, active_demand)
active_risk = assess_inventory_risk(active_stock, active_demand, eta_hours=active_route_hours)

# Candidate replenishment sources
replenishment_sources = find_replenishment_sources(
    inventory=base_inventory,
    product="Emergency medicine",
    exclude="Hospital",
    required_units=active_demand * (active_route_hours or 4.0)
)

# Run Recovery Decision Engine
recovery_result = recommend_recovery(
    route=active_route,
    route_hours=active_route_hours,
    route_km=active_route_km,
    stockout_hours=active_stock_cover,
    sources=replenishment_sources,
    priority=st.session_state.recovery_priority,
    transfer_cost_per_unit=st.session_state.transfer_cost_per_unit,
    destination_stock=active_stock,
    demand_per_hour=active_demand,
    roads=active_roads
)


# -----------------------------------------------------------------------------
# 6. HEADER & SYSTEM STATUS BANNER
# -----------------------------------------------------------------------------
scenario_badge_class = "badge-live" if st.session_state.scenario == "Normal operations" else "badge-sim"

st.markdown(f"""
<div class="brand-header">
    <div>
        <div class="brand-title">
            <span>🛡️ SUPPLYGUARD AI</span>
            <span class="badge-pill {scenario_badge_class}">{st.session_state.scenario.upper()}</span>
            <span class="badge-pill badge-sim">SIMULATED LOGISTICS TELEMETRY</span>
        </div>
        <div class="brand-subtitle">
            Autonomous Logistics Crisis Control Tower • Dijkstra Shortest-Path Routing • Explainable Recovery Engine
        </div>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Network Telemetry</div>
        <div style="font-size: 0.95rem; font-weight: 600; color: {'#34D399' if active_route else '#EF4444'};">
            {'● CORRIDOR ACTIVE' if active_route else '▲ CORRIDOR SEVERED'}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 7. SECTION 2: CRISIS CONTROL CENTER (TOP METRICS RIBBON)
# -----------------------------------------------------------------------------
# Dynamic metrics calculated strictly from real data
total_shipments = len(raw_shipments)
delayed_shipments = int(raw_shipments["Status"].isin(["Delayed"]).sum())
at_risk_shipments = int(raw_shipments["Status"].isin(["At risk"]).sum())
ontime_shipments = int(raw_shipments["Status"].isin(["On time"]).sum())

stock_cover_text = format_stock_cover(active_stock_cover)
eta_text = f"{active_route_hours:.2f} hrs" if active_route_hours is not None else "No Open Route"

m1, m2, m3, m4, m5, m6 = st.columns(6)

with m1:
    st.markdown(f"""
    <div class="sg-metric-card">
        <div class="sg-metric-label">Tracked Shipments</div>
        <div class="sg-metric-value">{total_shipments}</div>
        <div class="sg-metric-delta delta-neutral">{ontime_shipments} on time • {delayed_shipments + at_risk_shipments} alerts</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    status_color_class = "delta-negative" if (delayed_shipments + at_risk_shipments) > 0 else "delta-positive"
    st.markdown(f"""
    <div class="sg-metric-card">
        <div class="sg-metric-label">Shipments at Risk</div>
        <div class="sg-metric-value" style="color: {'#EF4444' if at_risk_shipments > 0 else '#F8FAFC'};">{at_risk_shipments}</div>
        <div class="sg-metric-delta {status_color_class}">{delayed_shipments} delayed in transit</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="sg-metric-card">
        <div class="sg-metric-label">Destination Stock</div>
        <div class="sg-metric-value">{int(active_stock)} <span style="font-size: 0.9rem; font-weight: normal; color: #94A3B8;">units</span></div>
        <div class="sg-metric-delta delta-neutral">Burn: {active_demand:.1f} units/hr</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    cover_color = "#34D399" if active_stock_cover >= (active_route_hours or 4.0) else "#EF4444"
    st.markdown(f"""
    <div class="sg-metric-card">
        <div class="sg-metric-label">Stock Cover Runway</div>
        <div class="sg-metric-value" style="color: {cover_color};">{stock_cover_text}</div>
        <div class="sg-metric-delta {'delta-positive' if active_risk['urgency'] == 'LOW' else 'delta-negative'}">{active_risk['status']}</div>
    </div>
    """, unsafe_allow_html=True)

with m5:
    route_status_label = "Optimal Path" if active_route else "Severed"
    st.markdown(f"""
    <div class="sg-metric-card">
        <div class="sg-metric-label">Route ETA to Destination</div>
        <div class="sg-metric-value" style="color: {'#38BDF8' if active_route else '#EF4444'};">{eta_text}</div>
        <div class="sg-metric-delta delta-neutral">{' → '.join(active_route) if active_route else 'No path open'}</div>
    </div>
    """, unsafe_allow_html=True)

with m6:
    rec_cost = recovery_result.get("estimated_recovery_cost", 0.0)
    st.markdown(f"""
    <div class="sg-metric-card">
        <div class="sg-metric-label">Estimated Recovery Cost</div>
        <div class="sg-metric-value">${rec_cost:.2f}</div>
        <div class="sg-metric-delta delta-neutral">Objective: {st.session_state.recovery_priority}</div>
    </div>
    """, unsafe_allow_html=True)


st.write("")  # Vertical spacer


# -----------------------------------------------------------------------------
# 8. MAIN NAVIGATION TABS
# -----------------------------------------------------------------------------
tab_simulator, tab_shipments, tab_inventory, tab_logs = st.tabs([
    "🚨 Crisis Simulator & Route Optimization",
    "🚚 Shipment Monitor & Live Telemetry",
    "📦 Inventory Risk & Replenishment Matrix",
    "📜 Simulated Activity & Audit Log"
])


# =============================================================================
# TAB 1: CRISIS SIMULATOR & ROUTE OPTIMIZATION
# =============================================================================
with tab_simulator:
    st.markdown("### ⚡ Crisis Impact & Autonomous Recovery Planning")
    
    # -------------------------------------------------------------------------
    # SECTION 8: BEFORE-AND-AFTER IMPACT COMPARISON PANEL
    # -------------------------------------------------------------------------
    st.markdown("#### ⚖️ Before-and-After Disruption Impact Comparison")
    
    # Delta calculations
    time_delta = round(active_route_hours - base_route_hours, 2) if (active_route_hours and base_route_hours) else None
    km_delta = round(active_route_km - base_route_km, 1) if (active_route_km and base_route_km) else None
    cover_delta = round(active_stock_cover - base_stock_cover, 1) if not (math.isinf(active_stock_cover) or math.isinf(base_stock_cover)) else None
    cost_delta = round(rec_cost - base_cost, 2)

    c_b1, c_b2, c_b3, c_b4, c_b5 = st.columns(5)
    
    with c_b1:
        st.markdown(f"""
        <div class="comp-box">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Active Route Corridor</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #38BDF8; margin: 6px 0;">{' → '.join(active_route) if active_route else 'None (Blocked)'}</div>
            <div style="font-size: 0.75rem; color: #64748B;">Baseline: {' → '.join(base_route)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c_b2:
        time_str = f"{active_route_hours:.2f} hrs" if active_route_hours else "Blocked"
        delta_str = f"+{time_delta:.2f}h delay" if time_delta and time_delta > 0 else (f"{time_delta:.2f}h" if time_delta else "N/A")
        delta_color = "#EF4444" if time_delta and time_delta > 0 else "#34D399"
        st.markdown(f"""
        <div class="comp-box">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Delivery Transit Time</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC; margin: 4px 0;">{time_str}</div>
            <div style="font-size: 0.78rem; color: {delta_color}; font-weight: 600;">{delta_str} (Baseline: {base_route_hours:.2f}h)</div>
        </div>
        """, unsafe_allow_html=True)

    with c_b3:
        cover_str = format_stock_cover(active_stock_cover)
        cov_delta_str = f"{cover_delta:+.1f}h" if cover_delta is not None else "N/A"
        cov_color = "#34D399" if cover_delta and cover_delta >= 0 else "#EF4444"
        st.markdown(f"""
        <div class="comp-box">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Stock Cover Runway</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC; margin: 4px 0;">{cover_str}</div>
            <div style="font-size: 0.78rem; color: {cov_color}; font-weight: 600;">{cov_delta_str} (Baseline: {base_stock_cover:.1f}h)</div>
        </div>
        """, unsafe_allow_html=True)

    with c_b4:
        stockout_gap = round((active_route_hours or 0.0) - active_stock_cover, 1)
        if not active_route:
            stockout_label = "Complete Severance"
            gap_color = "#EF4444"
        elif active_stock_cover < (active_route_hours or 0.0):
            stockout_label = f"Deficit: {stockout_gap}h before delivery"
            gap_color = "#EF4444"
        else:
            buffer_h = round(active_stock_cover - (active_route_hours or 0.0), 1)
            stockout_label = f"Buffer: +{buffer_h}h safety margin"
            gap_color = "#34D399"
            
        st.markdown(f"""
        <div class="comp-box">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Pre-Delivery Stockout Risk</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: {gap_color}; margin: 6px 0;">{stockout_label}</div>
            <div style="font-size: 0.75rem; color: #64748B;">Baseline: Secure (+{round(base_stock_cover - base_route_hours, 1)}h buffer)</div>
        </div>
        """, unsafe_allow_html=True)

    with c_b5:
        cost_delta_str = f"+${cost_delta:.2f}" if cost_delta > 0 else f"${cost_delta:.2f}"
        st.markdown(f"""
        <div class="comp-box">
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Projected Recovery Cost</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #F8FAFC; margin: 4px 0;">${rec_cost:.2f}</div>
            <div style="font-size: 0.78rem; color: {'#F59E0B' if cost_delta > 0 else '#34D399'}; font-weight: 600;">{cost_delta_str} vs Base (${base_cost:.2f})</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # -------------------------------------------------------------------------
    # SECTION 6: INTERACTIVE NETWORK MAP & DIJKSTRA ROUTE BREAKDOWN
    # -------------------------------------------------------------------------
    col_map, col_plan = st.columns([1.35, 1])

    with col_map:
        st.markdown("#### 🗺️ Network Topology & Shortest-Path Visualization")
        st.caption("Modeled logistics graph with nodes and weighted road edges. Active Dijkstra shortest path highlighted in cyan.")

        # Build Interactive Plotly 2D Network Map
        fig = go.Figure()

        # 1. Draw all roads (edges)
        for (u, v), edge in active_roads.items():
            if u not in NODE_METADATA or v not in NODE_METADATA:
                continue
            x0, y0 = NODE_METADATA[u]["x"], NODE_METADATA[u]["y"]
            x1, y1 = NODE_METADATA[v]["x"], NODE_METADATA[v]["y"]

            is_open = edge.get("open", True)
            hours = edge.get("hours", 1.0)
            km = edge.get("km", 10.0)
            condition = edge.get("condition", "Normal")

            # Check if this edge is part of active shortest path
            is_in_path = False
            if active_route and len(active_route) >= 2:
                for idx in range(len(active_route) - 1):
                    if set([active_route[idx], active_route[idx + 1]]) == set([u, v]):
                        is_in_path = True
                        break

            # Line styling based on condition and active path
            if not is_open:
                line_color = "rgba(239, 68, 68, 0.7)"  # Red dashed for blocked
                line_dash = "dash"
                line_width = 2.5
                hover_text = f"❌ <b>BLOCKED ROUTE</b><br>{u} ↔ {v}<br>Distance: {km:.1f} km<br>Status: Road Closed"
            elif is_in_path:
                line_color = "#00F2FE"  # Glowing cyan for active path
                line_dash = "solid"
                line_width = 4.5
                hover_text = f"🚀 <b>ACTIVE SHORTEST PATH</b><br>{u} ↔ {v}<br>Time: {hours:.2f} hrs<br>Distance: {km:.1f} km<br>Condition: {condition}"
            elif "Congestion" in condition or hours > DEFAULT_ROADS.get((u, v), DEFAULT_ROADS.get((v, u), {})).get("hours", 0) * 1.5:
                line_color = "rgba(245, 158, 11, 0.7)"  # Amber for traffic
                line_dash = "dot"
                line_width = 3.0
                hover_text = f"⚠️ <b>HEAVY TRAFFIC DELAY</b><br>{u} ↔ {v}<br>Time: {hours:.2f} hrs<br>Distance: {km:.1f} km<br>Condition: {condition}"
            else:
                line_color = "rgba(148, 163, 184, 0.35)"  # Slate for normal idle edge
                line_dash = "solid"
                line_width = 2.0
                hover_text = f"🛣️ <b>OPEN CORRIDOR</b><br>{u} ↔ {v}<br>Time: {hours:.2f} hrs<br>Distance: {km:.1f} km<br>Condition: {condition}"

            fig.add_trace(go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color=line_color, width=line_width, dash=line_dash),
                hoverinfo="text",
                hovertext=hover_text,
                showlegend=False
            ))

            # Add mid-point text label for edge time
            mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
            edge_tag = f"{hours:.2f}h" if is_open else "BLOCKED"
            tag_color = "#EF4444" if not is_open else ("#00F2FE" if is_in_path else "#94A3B8")
            fig.add_trace(go.Scatter(
                x=[mid_x],
                y=[mid_y],
                mode="text",
                text=[edge_tag],
                textposition="middle center",
                textfont=dict(size=9, color=tag_color, family="monospace"),
                hoverinfo="none",
                showlegend=False
            ))

        # 2. Draw nodes
        node_x = [meta["x"] for meta in NODE_METADATA.values()]
        node_y = [meta["y"] for meta in NODE_METADATA.values()]
        node_names = list(NODE_METADATA.keys())
        node_colors = [meta["color"] for meta in NODE_METADATA.values()]
        node_types = [meta["type"] for meta in NODE_METADATA.values()]
        node_symbols = ["square" if "Central" in k else ("cross" if "Hospital" in k else "diamond") for k in node_names]
        node_hover = [
            f"📍 <b>{name}</b><br>Role: {NODE_METADATA[name]['type']}<br>{NODE_METADATA[name]['description']}"
            + (f"<br>Current Stock: {active_stock:.0f} units | Demand: {active_demand:.1f}/h" if name == "Hospital" else "")
            for name in node_names
        ]

        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker=dict(size=24, color=node_colors, symbol=node_symbols, line=dict(color="#FFFFFF", width=1.5)),
            text=[f"<b>{name}</b>" for name in node_names],
            textposition=["bottom center" if "Hospital" in n else ("top center" if "North" in n else "middle right") for n in node_names],
            textfont=dict(size=11, color="#F8FAFC"),
            hoverinfo="text",
            hovertext=node_hover,
            showlegend=False
        ))

        # Layout styling
        fig.update_layout(
            paper_bgcolor="#0A0F1D",
            plot_bgcolor="#0E1729",
            margin=dict(l=15, r=15, t=15, b=15),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 11]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0.5, 11]),
            height=370,
            hoverlabel=dict(bgcolor="#1E293B", font_size=12, font_color="#F8FAFC", font_family="monospace")
        )
        st.plotly_chart(fig, use_container_width=True)

        # Route Breakdown Details
        if active_route:
            st.markdown(f"**Computed Path**: `{' → '.join(active_route)}` ({active_route_hours:.2f} hrs, {active_route_km:.1f} km)")
            # Leg table
            legs = []
            for i in range(len(active_route) - 1):
                u, v = active_route[i], active_route[i + 1]
                details = get_edge_details(active_roads, u, v) or {}
                legs.append({
                    "Leg": f"Leg {i+1}",
                    "From": u,
                    "To": v,
                    "Distance (km)": f"{details.get('km', 0.0):.1f}",
                    "Travel Time": f"{details.get('hours', 0.0):.2f} hrs",
                    "Condition": details.get("condition", "Normal")
                })
            st.dataframe(pd.DataFrame(legs), use_container_width=True, hide_index=True)
        else:
            st.error("⚠️ All modeled delivery paths between Central Warehouse and Hospital are currently blocked.")

    # -------------------------------------------------------------------------
    # SECTION 7: RECOVERY DECISION ENGINE & CANDIDATE ACTION COMPARISON
    # -------------------------------------------------------------------------
    with col_plan:
        st.markdown("#### 🧠 Autonomous Recovery Decision Engine")
        
        # Strategy callout banner
        urgency_class = recovery_result["urgency"].lower()
        st.markdown(f"""
        <div class="strategy-card {urgency_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; color: {'#EF4444' if urgency_class=='critical' else ('#F59E0B' if urgency_class=='high' else '#10B981')};">
                    PRIORITY ACTION • {recovery_result['urgency']}
                </span>
                <span style="font-size: 0.75rem; color: #94A3B8;">Goal: {st.session_state.recovery_priority}</span>
            </div>
            <div style="font-size: 1.15rem; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">
                {recovery_result['action']}
            </div>
            <div style="font-size: 0.86rem; color: #CBD5E1; line-height: 1.45;">
                {recovery_result['reason']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Explainable System Rationale:**")
        for reason in recovery_result["explanations"]:
            st.markdown(f"- <span style='font-size: 0.86rem; color: #E2E8F0;'>{reason}</span>", unsafe_allow_html=True)

        st.write("")
        st.markdown("**Candidate Recovery Options Evaluated:**")
        
        options_list = recovery_result.get("options", [])
        if options_list:
            opt_rows = []
            for opt in options_list:
                status_icon = "★ " if opt.get("is_recommended") else ""
                opt_rows.append({
                    "Option": f"{status_icon}{opt['title']}",
                    "Category": opt["category"],
                    "Time (hrs)": f"{opt['estimated_time_hours']:.2f}" if opt["estimated_time_hours"] else "N/A",
                    "Cost ($)": f"${opt['estimated_cost_usd']:.2f}" if opt["estimated_cost_usd"] is not None else "N/A",
                    "Stockout Prevented": "✓ Yes" if opt["stockout_prevented"] else "✗ No",
                    "Priority Score": f"{opt.get('score', 0.0):.1f}"
                })
            st.dataframe(pd.DataFrame(opt_rows), use_container_width=True, hide_index=True)
            
            # Show assumptions for top recommended
            top_opt = recovery_result.get("best_option")
            if top_opt:
                st.info(f"**Assumptions & Risks for Recommended Action:** {top_opt.get('risks_and_assumptions')}")
        else:
            st.warning("No feasible recovery options generated for current constraints.")


# =============================================================================
# TAB 2: SHIPMENT MONITOR
# =============================================================================
with tab_shipments:
    st.markdown("### 🚚 Real-Time Shipment Telemetry Monitor")
    st.caption("Active supply pipeline tracking across regional hubs. Simulated live logistics stream.")

    # Search and Filtering Controls
    f_c1, f_c2, f_c3 = st.columns([1.5, 1, 1])
    search_query = f_c1.text_input("🔍 Search Shipments", placeholder="Search by Shipment ID or Cargo Product...")
    status_filter = f_c2.selectbox("Filter by Status", ["All Statuses", "On time", "Delayed", "At risk"])
    priority_filter = f_c3.selectbox("Filter by Priority", ["All Priorities", "Critical", "High", "Medium", "Low"])

    # Filter shipments dataframe
    filtered_df = raw_shipments.copy()
    if search_query:
        query_mask = (
            filtered_df["Shipment"].str.contains(search_query, case=False, na=False) |
            filtered_df["Product"].str.contains(search_query, case=False, na=False)
        )
        filtered_df = filtered_df[query_mask]

    if status_filter != "All Statuses":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]

    if priority_filter != "All Priorities":
        filtered_df = filtered_df[filtered_df["Priority"] == priority_filter]

    # Dynamically inject live risk alerts based on simulated scenario
    def compute_shipment_alert(row):
        ship_id = row["Shipment"]
        dest = row["Destination"]
        eta = row.get("ETA (hours)", 0.0)

        if dest == "Hospital" and st.session_state.scenario == "Main route blocked":
            return "🚨 Rerouted via alternate corridor; monitor arrival buffer"
        elif dest == "Hospital" and active_stock_cover < eta:
            return f"⚠️ High risk: Destination stock cover ({active_stock_cover:.1f}h) < ETA ({eta:.1f}h)"
        elif row["Status"] == "Delayed":
            return "⚠️ Road transit delay reported on inbound link"
        elif row["Status"] == "At risk":
            return "🚨 Inventory shortfall risk at destination node"
        return "✓ Route nominal and on schedule"

    filtered_df["System Alerts & Risk Assessment"] = filtered_df.apply(compute_shipment_alert, axis=1)

    # Display styled shipments table
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Shipment": st.column_config.TextColumn("Shipment ID", width="small"),
            "Product": st.column_config.TextColumn("Cargo Manifest", width="medium"),
            "Origin": st.column_config.TextColumn("Origin Node"),
            "Destination": st.column_config.TextColumn("Destination Node"),
            "Status": st.column_config.TextColumn("Telemetry Status"),
            "ETA (hours)": st.column_config.NumberColumn("ETA (hours)", format="%.1f hrs"),
            "Priority": st.column_config.TextColumn("Priority"),
            "System Alerts & Risk Assessment": st.column_config.TextColumn("Real-Time Operational Alert", width="large")
        }
    )

    st.write("")
    s_col1, s_col2 = st.columns([1, 1])
    
    with s_col1:
        st.markdown("#### 📊 Fleet Status Distribution")
        status_counts = raw_shipments["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Shipment Count"]
        
        color_map = {"On time": "#10B981", "Delayed": "#F59E0B", "At risk": "#EF4444"}
        fig_status = px.pie(
            status_counts,
            names="Status",
            values="Shipment Count",
            color="Status",
            color_discrete_map=color_map,
            hole=0.55
        )
        fig_status.update_layout(
            paper_bgcolor="#0A0F1D",
            plot_bgcolor="#0A0F1D",
            margin=dict(l=10, r=10, t=10, b=10),
            height=260,
            font_color="#F8FAFC",
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with s_col2:
        st.markdown("#### 📦 Priority Breakdown")
        prio_counts = raw_shipments["Priority"].value_counts().reset_index()
        prio_counts.columns = ["Priority", "Shipments"]
        fig_prio = px.bar(
            prio_counts,
            x="Priority",
            y="Shipments",
            color="Priority",
            color_discrete_map={"Critical": "#EF4444", "High": "#F59E0B", "Medium": "#38BDF8", "Low": "#94A3B8"}
        )
        fig_prio.update_layout(
            paper_bgcolor="#0A0F1D",
            plot_bgcolor="#0E1729",
            margin=dict(l=10, r=10, t=10, b=10),
            height=260,
            font_color="#F8FAFC",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
        )
        st.plotly_chart(fig_prio, use_container_width=True)


# =============================================================================
# TAB 3: INVENTORY RISK ANALYSIS & REPLENISHMENT MATRIX
# =============================================================================
with tab_inventory:
    st.markdown("### 📦 Destination Inventory Risk & Multi-Echelon Stock Runway")
    st.caption("Verifiable mathematical calculations modeling stock depletion rates against delivery transit windows.")

    # Mathematical Formula Callout
    st.markdown(f"""
    <div style="background: #111A2E; border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 14px 18px; margin-bottom: 20px;">
        <div style="font-size: 0.78rem; text-transform: uppercase; color: #38BDF8; font-weight: 700; letter-spacing: 0.5px;">Mathematical Formulation</div>
        <div style="font-size: 1.05rem; font-weight: 600; color: #F8FAFC; margin: 4px 0;">
            Stock Cover (Hours) = Available Stock ({active_stock:.0f} units) ÷ Hourly Demand ({active_demand:.1f} units/hr) = <span style="color: {'#34D399' if active_stock_cover >= (active_route_hours or 4.0) else '#EF4444'};">{stock_cover_text}</span>
        </div>
        <div style="font-size: 0.82rem; color: #94A3B8;">
            Safety Margin vs Delivery ETA ({eta_text}): <b>{active_risk['explanation']}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    inv_c1, inv_c2 = st.columns([1.2, 1])

    with inv_c1:
        st.markdown("#### 🏢 Network-Wide Warehouse Inventory")
        inv_display = base_inventory.copy()
        inv_display["Hourly Burn (units/h)"] = (inv_display["Daily demand"] / 24.0).round(2)
        inv_display["Stock Cover (hours)"] = inv_display.apply(
            lambda r: round(stockout_hours(r["Stock"], r["Daily demand"] / 24.0), 1), axis=1
        )
        inv_display["Runway Status"] = inv_display["Stock Cover (hours)"].apply(
            lambda h: "Critical (<12h)" if h < 12 else ("Moderate (12-24h)" if h < 24 else "Adequate (>24h)")
        )

        st.dataframe(
            inv_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Warehouse": st.column_config.TextColumn("Warehouse Node"),
                "Product": st.column_config.TextColumn("Product SKU"),
                "Stock": st.column_config.NumberColumn("Current Stock (units)"),
                "Daily demand": st.column_config.NumberColumn("Daily Demand (units/day)"),
                "Hourly Burn (units/h)": st.column_config.NumberColumn("Burn Rate (u/h)", format="%.2f"),
                "Stock Cover (hours)": st.column_config.NumberColumn("Stock Cover (hrs)", format="%.1f hrs"),
                "Runway Status": st.column_config.TextColumn("Stock Health")
            }
        )

    with inv_c2:
        st.markdown("#### 🔄 Replenishment Sources Radar (Emergency Medicine)")
        if replenishment_sources:
            sources_df = pd.DataFrame(replenishment_sources)
            st.dataframe(
                sources_df[["Warehouse", "Available stock", "Local cover (hours)", "Transferable surplus", "Can fulfill demand"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Warehouse": st.column_config.TextColumn("Candidate Depot"),
                    "Available stock": st.column_config.NumberColumn("On-Hand (units)"),
                    "Local cover (hours)": st.column_config.NumberColumn("Depot Cover (hrs)", format="%.1f hrs"),
                    "Transferable surplus": st.column_config.NumberColumn("Safe Surplus", format="%d units"),
                    "Can fulfill demand": st.column_config.CheckboxColumn("Fulfills Deficit?")
                }
            )
            st.caption("Safe surplus reserves 12 hours of local demand at the source depot before authorizing inter-hub transfers.")
        else:
            st.error("No candidate replenishment warehouse with available inventory was detected in the distribution network.")


# =============================================================================
# TAB 4: SIMULATED ACTIVITY LOG & AUDIT TRAIL
# =============================================================================
with tab_logs:
    st.markdown("### 📜 Simulated System Activity & Audit Trail")
    st.caption("Chronological record of simulated crisis events, Dijkstra route re-solves, and recovery decisions.")

    log_c1, log_c2 = st.columns([3, 1])
    with log_c2:
        if st.button("🧹 Clear Event Log", use_container_width=True):
            st.session_state.event_log = []
            log_event("LOG_CLEARED", "System", "Audit log cleared by operator.", "NORMAL")
            st.rerun()

    if st.session_state.event_log:
        logs_df = pd.DataFrame(st.session_state.event_log)
        # Reverse to show newest on top
        logs_display = logs_df.iloc[::-1].reset_index(drop=True)
        st.dataframe(
            logs_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Timestamp": st.column_config.TextColumn("Timestamp (Simulated)", width="small"),
                "Event Type": st.column_config.TextColumn("Event", width="medium"),
                "Component": st.column_config.TextColumn("Subsystem", width="small"),
                "Details": st.column_config.TextColumn("Telemetry & Action Description", width="large"),
                "Status": st.column_config.TextColumn("Status Badge", width="small")
            }
        )
    else:
        st.info("No events logged yet in current session.")


# -----------------------------------------------------------------------------
# FOOTER & PROJECT ARCHITECTURE DISCLOSURE
# -----------------------------------------------------------------------------
st.divider()
f_left, f_right = st.columns([2, 1])

with f_left:
    st.markdown("""
    **SupplyGuard AI — Architectural Notes & Operational Boundary:**
    - **Routing Algorithm**: Exact Dijkstra Shortest-Path implementation on weighted graph edges (`route_optimizer.py`).
    - **Inventory Formulations**: Deterministic runway and pre-delivery deficit buffer analysis (`inventory.py`).
    - **Recovery Engine**: Rule-based explainable multi-criteria ranking comparing rerouting, stock transfers, and monitoring (`recovery_engine.py`).
    - **Data Integrity**: Uses simulated logistics telemetry. No black-box ML claims; all reasoning is mathematically auditable.
    """)

with f_right:
    st.markdown("""
    <div style="text-align: right; color: #64748B; font-size: 0.8rem;">
        SupplyGuard AI v2.5 Enterprise Edition<br>
        Built with Streamlit & Plotly<br>
        Ready for Streamlit Community Cloud
    </div>
    """, unsafe_allow_html=True)
