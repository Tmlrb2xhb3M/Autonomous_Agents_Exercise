from typing import Dict, List, Any
from smolagents import tool
from world import WORLD_STATE

# Tool Execution Helper 
def execute_tool(tool_name: str, tool_args: dict):
    """Execute a tool by name with given arguments."""
    tool = ALL_TOOLS.get(tool_name)
    if tool is None:
        return {"error": f"Tool '{tool_name}' not found"}
    
    try:
        result = tool(**tool_args)
        return result
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}

# Tool Implementations
@tool
def detect_failure_nodes() -> List[str]:
    """
    Returns a list of node IDs that are currently in failure state.
    The agent uses this to detect which infrastructure elements need repair.
    Returns:
        list of str: IDs of nodes with status 'failed'.
    """
    step_simulation_time()
    global WORLD_STATE
    failed = [
        node_id
        for node_id, node in WORLD_STATE["nodes"].items()
        if node["status"] == "failed"
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
def get_available_crews() -> Dict[str, Any]:
    """
    Returns information about available repair crews (only crews with availability=True).
    
    Returns:
        dict: A dictionary where keys are crew IDs and values contain crew details:
            {
                "Crew_A": {
                    "skills": ["water"],
                    "availability": True,
                    "current_node": None
                },
                ...
            }
            Only includes crews that are currently available.
    """
    global WORLD_STATE
    crews_info = {}
    for crew_id, crew in WORLD_STATE["crews"].items():
        if crew["availability"]:
            crews_info[crew_id] = {
                "skills": crew["skills"],
                "availability": crew["availability"],
                "current_node": crew["current_node"]
            }
    return crews_info

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
    step_simulation_time()
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

        crew["availability"] = False
        crew["current_node"] = node_id
        crew["assigned_at"] = WORLD_STATE["simulation_time"]
        node["status"] = "in_repair"
        node["repair_start_time"] = WORLD_STATE["simulation_time"]
        node["repair_duration"] = 8  if node["criticality"] == "High" else 5

        assignments[crew_id] = node_id

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
        "updated_nodes": updated_nodes,
        "simulation_time": WORLD_STATE["simulation_time"]
    }

def step_simulation_time():
    global WORLD_STATE
    WORLD_STATE["simulation_time"] += 1
    for node_id, node in WORLD_STATE["nodes"].items():
        if(node["status"] == "in_repair" and WORLD_STATE["simulation_time"] >= node["repair_start_time"] + node["repair_duration"]):
            crew_id = None
            for c_id, crew in WORLD_STATE["crews"].items():
                if crew["current_node"] == node_id:
                    crew["availability"] = True
                    crew["current_node"] = None
                    crew["assigned_at"] = None
                    crew_id = c_id
                    break
            node["status"] = "repaired"


# Tool Configurations
ALL_TOOLS = {
    "detect_failure_nodes": detect_failure_nodes,
    "estimate_impact": estimate_impact,
    "assign_repair_crew": assign_repair_crew,
    "get_available_crews": get_available_crews
}

# Tool Registries
FAILURE_DETECTION_TOOLS = [detect_failure_nodes]

IMPACT_ANALYSIS_TOOLS = [estimate_impact]

PLANNER_TOOL_REGISTRY = [get_available_crews]

REPAIR_EXECUTOR_TOOLS = [assign_repair_crew, get_available_crews]
