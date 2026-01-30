from typing import Dict, List, Any
from smolagents import tool
from world import WORLD_STATE

@tool
def detect_failure_nodes() -> List[str]:
    """
    Returns a list of node IDs that are currently in failure state.
    The agent uses this to detect which infrastructure elements need repair.
    Returns:
        list of str: IDs of nodes with status 'failed'.
    """
    global WORLD_STATE
    failed = [
        node_id
        for node_id, info in WORLD_STATE["nodes"].items()
        if info["status"] == "failed"
    ]
    return failed

@tool
def estimate_impact(node_id: str) -> Dict[str, object]:
    """
    Estimates the social and operational impact of a failed node.
    Args:
        node_id: The identifier of the node (e.g., 'Pipe_42', 'Server_B').
    Returns:
        dict: Metrics describing impact, for example:
            {
                "population_affected": int,
                "criticality": "Low" | "Medium" | "High"
            }
        If the node does not exist, returns a dict with an 'error' field.
    """
    global WORLD_STATE
    node = WORLD_STATE["nodes"].get(node_id)
    if node is None:
        return{"Error": f"Unknown node_id: {node_id}"}
    return{
        "population_affected": node["population_affected"],
        "criticality": node["criticality"]
    }

@tool
def assign_repair_crew(node_ids: List[str], crew_ids: List[str]) -> Dict[str,Any]:
    """
    Assigns repair crews to failed nodes and updates the global world state.
    
    IMPORTANT: This permanently changes crew availability and node status until 
    manually reset or future repair completion logic is implemented.
    
    Args:
        node_ids: List of node IDs that should be repaired (e.g., ["Pipe_42", "Server_B"]).
        crew_ids: List of crew IDs to assign (must match node_ids in length).
    
    Returns:
        dict: Contains:
            - "assignments": dict of successful crew_id -> node_id mappings
            - "total_estimated_time": int (hours)
            - "failures": list of failure reasons
            - "updated_crews": list of affected crew IDs (now unavailable)
            - "updated_nodes": list of nodes now "in_repair"
    
    Example:
        assign_repair_crew(["Pipe_42"], ["Crew_A"]) 
        -> {"assignments": {"Crew_A": "Pipe_42"}, "updated_crews": ["Crew_A"]}
    """
    global WORLD_STATE
    assignments = {}
    failures = []
    total_time = 0
    updated_crews = []
    updated_nodes = []
    for crew_id, node_id in zip(crew_ids, node_ids):
        crew = WORLD_STATE["crews"].get(crew_id)
        node = WORLD_STATE["nodes"].get(node_id)
        if crew is None or node is None:
            failures.append(f"Invalid crew_id or node_id: {crew_id}, {node_id}")
            continue
        if not crew["availability"]:
            failures.append(f"{crew_id} is not available")
            continue
        if node["status"] != "failed":
            failures.append(f"{node_id} is not in failed state")
            continue
        if node["type"] not in crew["skills"]:
            failures.append(f"{crew_id} cannot repair node type {node['type']}")
            continue

        assignments[crew_id] = node_id
        crew["availability"] = False
        crew["current_node"] = node_id
        node["status"] = "in_repair"

        updated_crews.append(crew_id)
        updated_nodes.append(node_id)

        base_time = 3
        if node["criticality"] == "High":
            base_time += 2
        elif node["criticality"] == "Medium":
            base_time += 1
        total_time += base_time
    
    return{
        "assignments": assignments, 
        "total_estimated_time": total_time,
        "failures": failures,
        "updated_crews": updated_crews,
        "updated_nodes": updated_nodes
    }

# Tool Registries
OBSERVER_TOOL_REGISTRY = {
    "detect_failure_nodes": detect_failure_nodes,
    "estimate_impact": estimate_impact,
}