"""
SupplyGuard AI — Route Optimization & Network Modeling
Implements Dijkstra's algorithm for shortest-path calculation on a weighted logistics graph.
Supports road closures, traffic congestion, distance/time tracking, and network visualization helpers.
"""

import heapq
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any

# Canonical node metadata for simulation and visualization
NODE_METADATA: Dict[str, Dict[str, Any]] = {
    "Central Warehouse": {
        "x": 1.5,
        "y": 7.5,
        "type": "Origin / Central DC",
        "description": "Primary Distribution Center (Main supply stockpile)",
        "color": "#38BDF8"  # Cyan
    },
    "North Hub": {
        "x": 5.0,
        "y": 9.0,
        "type": "Transit Hub",
        "description": "Northern Cross-Dock Facility",
        "color": "#818CF8"  # Indigo
    },
    "East Hub": {
        "x": 8.0,
        "y": 6.5,
        "type": "Regional Hub",
        "description": "Eastern Buffer Depot & Staging Post",
        "color": "#A78BFA"  # Purple
    },
    "Hospital": {
        "x": 9.2,
        "y": 2.0,
        "type": "Critical Destination",
        "description": "Metro Emergency Medical Center (Destination)",
        "color": "#F43F5E"  # Rose / Red
    },
}

# Baseline network edges (undirected)
DEFAULT_ROADS: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("Central Warehouse", "North Hub"): {"km": 18.0, "hours": 0.60, "open": True, "condition": "Normal"},
    ("Central Warehouse", "East Hub"): {"km": 22.0, "hours": 0.80, "open": True, "condition": "Normal"},
    ("North Hub", "Hospital"): {"km": 12.0, "hours": 0.50, "open": True, "condition": "Normal"},
    ("East Hub", "Hospital"): {"km": 9.0, "hours": 0.40, "open": True, "condition": "Normal"},
    ("North Hub", "East Hub"): {"km": 10.0, "hours": 0.35, "open": True, "condition": "Normal"},
    ("Central Warehouse", "Hospital"): {"km": 38.0, "hours": 0.95, "open": True, "condition": "Normal"},
}


def build_network(roads: Dict[Tuple[str, str], Dict[str, Any]], only_open: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build an undirected adjacency list from the roads dictionary.
    Each road tuple (A, B) is mapped bidirectionally.
    """
    graph = defaultdict(list)
    for (a, b), details in roads.items():
        is_open = details.get("open", True)
        if only_open and not is_open:
            continue
        
        hours = float(details.get("hours", 1.0))
        km = float(details.get("km", 10.0))
        cond = details.get("condition", "Normal")

        graph[a].append({"to": b, "hours": hours, "km": km, "open": is_open, "condition": cond})
        graph[b].append({"to": a, "hours": hours, "km": km, "open": is_open, "condition": cond})
    return graph


def shortest_path(
    graph: Dict[str, List[Dict[str, Any]]],
    start: str,
    end: str,
    weight: str = "hours"
) -> Tuple[List[str], Optional[float], Optional[float]]:
    """
    Dijkstra's shortest-path algorithm.
    Guarantees that blocked edges are excluded.
    Returns:
        (path, total_hours, total_km)
        If no route exists, returns ([], None, None).
    """
    if start == end:
        return [start], 0.0, 0.0

    if start not in graph or end not in graph:
        # One of the nodes is isolated or disconnected
        return [], None, None

    # Priority queue stores tuples: (accumulated_cost, current_node, path_history, total_hours, total_km)
    queue: List[Tuple[float, str, List[str], float, float]] = [(0.0, start, [start], 0.0, 0.0)]
    best_cost: Dict[str, float] = {start: 0.0}

    while queue:
        cost, node, path, total_h, total_k = heapq.heappop(queue)

        if node == end:
            return path, round(total_h, 3), round(total_k, 2)

        if cost > best_cost.get(node, float("inf")):
            continue

        for edge in graph.get(node, []):
            if not edge.get("open", True):
                continue
            
            neighbor = edge["to"]
            edge_h = edge["hours"]
            edge_k = edge["km"]
            edge_cost = edge_h if weight == "hours" else edge_k
            new_cost = cost + edge_cost

            if new_cost < best_cost.get(neighbor, float("inf")):
                best_cost[neighbor] = new_cost
                new_h = total_h + edge_h
                new_k = total_k + edge_k
                heapq.heappush(queue, (new_cost, neighbor, path + [neighbor], new_h, new_k))

    return [], None, None


def find_alternative_paths(
    roads: Dict[Tuple[str, str], Dict[str, Any]],
    start: str,
    end: str,
    primary_path: List[str]
) -> List[Dict[str, Any]]:
    """
    Find viable alternative routes distinct from the primary route.
    Penalizes edges used in the primary path to discover secondary routing.
    """
    alternatives = []
    # Test alternative graph excluding one intermediate edge at a time from primary
    if len(primary_path) >= 2:
        for i in range(len(primary_path) - 1):
            u, v = primary_path[i], primary_path[i + 1]
            # Copy roads and temporarily disable this segment
            temp_roads = {k: v.copy() for k, v in roads.items()}
            for edge_key in temp_roads:
                if set(edge_key) == {u, v}:
                    temp_roads[edge_key]["open"] = False

            temp_graph = build_network(temp_roads, only_open=True)
            alt_path, alt_h, alt_k = shortest_path(temp_graph, start, end, weight="hours")
            
            if alt_path and alt_path != primary_path:
                # Check if this alternative is already discovered
                if not any(a["path"] == alt_path for a in alternatives):
                    alternatives.append({
                        "path": alt_path,
                        "hours": alt_h,
                        "km": alt_k,
                        "via": " → ".join(alt_path[1:-1]) if len(alt_path) > 2 else "Direct"
                    })

    # Sort alternatives by hours
    alternatives.sort(key=lambda x: x["hours"])
    return alternatives


def get_edge_details(roads: Dict[Tuple[str, str], Dict[str, Any]], u: str, v: str) -> Optional[Dict[str, Any]]:
    """Look up edge details irrespective of tuple order."""
    if (u, v) in roads:
        return roads[(u, v)]
    if (v, u) in roads:
        return roads[(v, u)]
    return None
