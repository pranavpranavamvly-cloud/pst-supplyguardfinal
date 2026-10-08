# 🛡️ SupplyGuard AI — Logistics Crisis Control Tower

> **An Autonomous Supply-Chain Crisis Monitoring, Route Optimization, and Explainable Recovery Platform**  
> *"Engineered for logistics dispatchers and supply-chain command centers to predict stockouts, dynamically reroute blocked corridors, and coordinate multi-depot emergency replenishments."*

---

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/plotly-5.20%2B-3F4F75.svg)](https://plotly.com/)
[![Dijkstra Routing](https://img.shields.io/badge/algorithm-Dijkstra_Shortest_Path-00F2FE.svg)]()
[![Explainable AI](https://img.shields.io/badge/decision_engine-Explainable_Rule_Based-10B981.svg)]()

---

## 📌 Executive Summary

Modern supply chains are highly vulnerable to localized crises: sudden bridge collapses, extreme traffic bottlenecks, medical demand surges, and warehouse stockouts. Traditional dispatch tools often operate in silos—leaving dispatchers unable to see how a transportation delay directly cascades into a downstream stockout.

**SupplyGuard AI** unites transportation routing, multi-echelon inventory modeling, and emergency recovery decision-making into a unified **Logistics Crisis Control Tower**. By coupling **Dijkstra’s shortest-path algorithm** with **deterministic inventory burn modeling**, SupplyGuard AI detects stockout deficits before they occur and synthesizes actionable, explainable recovery plans.

---

## ⚡ Core Capabilities & Subsystems

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SUPPLYGUARD AI PLATFORM                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  ROUTE OPTIMIZER │       │  INVENTORY ENGINE│       │ RECOVERY ENGINE  │
│  (route_optimizer)       │  (inventory.py)  │       │(recovery_engine) │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│• Dijkstra solver │       │• Stock cover (h) │       │• Reroute ranking │
│• Blocked edges   │       │• Burn-rate audit │       │• Depot transfers │
│• Alternative paths       │• Deficit windows │       │• Cost vs time    │
│• Interactive map │       │• Depot sourcing  │       │• Transparent logic
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

### 1. 🛡️ Crisis Control Center Dashboard
- **Real-Time Fleet Telemetry**: Live counters for total tracked shipments, on-time arrivals, transit delays, and at-risk cargo.
- **Dynamic KPI Ribbon**: Destination stock levels, inventory burn rates, stock cover runway, active route ETA, and projected recovery costs—calculated directly from data rather than hardcoded mockups.
- **Premium Control Tower UI**: Dark navy aesthetic (`#0A0F1D`) with subtle cyan (`#00F2FE`) and emerald (`#10B981`) telemetry accents, high-contrast metric cards, and responsive layout.

### 2. 🗺️ Dijkstra Route Optimizer & Interactive Network Map (`route_optimizer.py`)
- **Weighted Graph Modeling**: Logistics network modeled with nodes (Central DC, Transit Hubs, Regional Buffers, Critical Destinations) and bidirectional weighted edges.
- **Autonomous Rerouting**: Excludes blocked corridors and recalculates shortest path in milliseconds using Dijkstra's algorithm.
- **Interactive 2D Topology Map**: Built with Plotly, rendering open corridors, congested links, blocked paths (red dashed lines), and the active shortest path (glowing neon cyan).
- **Leg-by-Leg Turn Breakdown**: Step-by-step transit details including segment distances, travel durations, and condition assessments.

### 3. 📦 Deterministic Inventory Risk Analysis (`inventory.py`)
- **Mathematical Stock Cover**:
  $$\text{Stock Cover (Hours)} = \frac{\text{Available Stock (units)}}{\text{Hourly Demand (units/hour)}}$$
- **Pre-Delivery Deficit Detection**: Compares stock cover against shipment arrival ETA:
  $$\text{Safety Buffer (Hours)} = \text{Stock Cover} - \text{Delivery ETA}$$
  - **Deficit**: Flags when stock will exhaust *before* cargo arrives, computing the exact deficit window in hours.
  - **Zero-Demand Safety**: Safely handles zero consumption without division-by-zero crashes ($\infty$ runway).
- **Multi-Depot Replenishment Radar**: Discovers alternative depots with available surplus, reserving safe local operating stock (12h buffer) before authorizing inter-hub transfers.

### 4. 🧠 Explainable Recovery Decision Engine (`recovery_engine.py`)
- **Multi-Option Trade-off Evaluation**: Generates and ranks feasible recovery actions:
  1. *Dynamic Carrier Rerouting*: Dispatching cargo along alternate open corridors.
  2. *Emergency Inter-Hub Stock Transfers*: Hot-shot couriers deploying stock from nearest depot.
  3. *Passive Telemetry Monitoring*: When destination stock safely covers transit time.
  4. *Cross-Network Escalation*: Spot-market procurement when network severance is complete.
- **Priority-Weighted Objective Scoring**:
  - `Meet deadline first`: 70% weight on transit speed and stockout prevention.
  - `Minimize cost`: 60% weight on minimizing freight and handling charges.
  - `Balance cost and time`: Multi-criteria weighted optimization.
- **100% Explainable Rationale**: Transparent bullet-point explanations of why an action was chosen, including cost breakdowns and explicit operational assumptions.

### 5. ⚠️ Advanced Crisis Simulator & Impact Comparison
- **Automated Disruption Scenarios**:
  - `Normal operations`: Baseline nominal transit.
  - `Main route blocked`: Direct corridor severed; triggers Dijkstra reroute via regional hubs.
  - `Heavy traffic`: 2.6× transit multiplier on primary roads; evaluates whether alternate paths save time.
  - `Demand spike`: 70% surge in hourly consumption at destination; recalculates stockout runway.
- **Before-and-After Impact Matrix**: Side-by-side comparison cards and tables highlighting differences in route time, distance, stock cover, stockout deficit, and recovery costs with explicit unit deltas (`+1.32h`, `-$42.00`).
- **One-Click Baseline Restoration**: Restores all edges, stock levels, and demand settings to default states.

### 6. 📜 Chronological Audit & Activity Log
- Real-time event log tracking scenario changes, Dijkstra recalculations, inventory evaluations, and recovery decisions with timestamps.

---

## 📂 Project Structure

```text
supplyguard-ai/
├── app.py                   # Streamlit Control Tower UI & interactive views
├── route_optimizer.py       # Dijkstra shortest-path solver & network graph modeling
├── inventory.py             # Stock cover formulas, deficit gap, & depot sourcing
├── recovery_engine.py       # Multi-criteria explainable recovery decision engine
├── test_suite.py            # Automated test suite covering Test Cases A through H
├── requirements.txt         # Production Python dependencies
├── README.md                # System documentation, architecture, & setup guide
└── data/
    └── sample_shipments.csv # Canonical simulated shipment telemetry manifest
```

---

## 🚀 Quickstart & Local Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Git

### 1. Clone or Open Project
```bash
cd "c:\pranav study\PYTHON\notes\New folder (2)"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Validation Suite
Verify all 8 algorithmic test cases (A through H):
```bash
python test_suite.py
```

### 4. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Validation & Test Matrix (Test Cases A through H)

The project includes an automated test suite (`test_suite.py`) validating all required scenarios:

| Test Case | Scenario / Condition | Expected Behavior | Verification Status |
|:---|:---|:---|:---:|
| **Test A** | Normal operations with sufficient stock | Dijkstra finds fastest path; stock cover > ETA; urgency = `LOW`. | **PASSED (100%)** |
| **Test B** | Main route blocked with alternative route | Blocked edge excluded; Dijkstra successfully reroutes via hub. | **PASSED (100%)** |
| **Test C** | Main route blocked with NO alternative | Handles disconnected graph cleanly; returns `([], None, None)`; urgency = `CRITICAL`. | **PASSED (100%)** |
| **Test D** | Low destination stock & high demand | Correctly flags stockout deficit before shipment arrival. | **PASSED (100%)** |
| **Test E** | Alternative depot with zero / insufficient stock | Excludes empty warehouses; escalates when no sources have inventory. | **PASSED (100%)** |
| **Test F** | Zero demand or missing inventory data | Safe division handling ($\infty$ stock cover); no unhandled exceptions. | **PASSED (100%)** |
| **Test G** | Simulation reset to baseline | Perfectly restores original baseline edge states, stock, and ETA. | **PASSED (100%)** |
| **Test H** | Scenario calculation consistency | All 4 crisis scenarios yield valid routes, stock cover, and explainable options. | **PASSED (100%)** |

Run `python test_suite.py` at any time to re-verify the full test suite.

---

## ☁️ Deployment Guide (Streamlit Community Cloud)

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "feat: SupplyGuard AI v2.5 Enterprise Edition"
   git branch -M main
   git remote add origin https://github.com/<your-username>/supplyguard-ai.git
   git push -u origin main
   ```
2. **Deploy on Streamlit Cloud**:
   - Visit [share.streamlit.io](https://share.streamlit.io/)
   - Click **Create app**
   - Choose your repository: `supplyguard-ai`
   - Select branch: `main`
   - Set main file path: `app.py`
   - Click **Deploy**

---

## ⚖️ Engineering Transparency & Data Integrity

- **Simulated Logistics Telemetry**: All data feeds, shipment manifests, and GPS telemetry are simulated models intended for crisis mitigation demonstration.
- **Verifiable Deterministic Logic**: SupplyGuard AI does not use unvalidated "black-box" machine learning. Every route is mathematically proven by Dijkstra's algorithm, every stockout is an exact quotient of inventory and burn rate, and every recovery option follows transparent multi-criteria optimization.
