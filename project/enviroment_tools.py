from typing import Dict, List, Any
from smolagents import tool

WORLD_STATE = {
    "nodes":{
        "Pipe_40":{
            "type": "water",
            "area": "District_B",
            "population_affected" : 500,
            "criticality" : "Medium",
            "status" : "failed"
        },
        "Pipe_20":{
            "type": "water",
            "area": "District_A",
            "population_affected" : 1000,
            "criticality" : "High",
            "status" : "failed"
        },
        "Server_A":{
            "type": "network",
            "area": "DataCenter_1",
            "population_affected" : 2000,
            "criticality" : "High",
            "status" : "failed"
        },
        "Tower_3":{
            "type": "telecom",
            "area": "District_C",
            "population_affected" : 1500,
            "criticality" : "Low",
            "status" : "working"
        }
    },
    "crews":{
        "Crew_A": {
            "skills": ["water"],
            "availability": True,
            "current_node": None
        },
        "Crew_B": {
            "skills": ["network","telecom"],
            "availability": True,
            "current_node": None
        },"Crew_C": {
            "skills": ["water", "telecom"],
            "availability": False,
            "current_node": "Pipe_5"
        }
    }
}

@tool
def detect_failure_nodes() -> List[str]:
    global WORLD_STATE
    failed = [
        node_id
        for node_id, info in WORLD_STATE["nodes"].items()
        if info["status"] == "failed"
    ]
    return failed
"""
Επιστρέφει μια λίστα με τα IDs των nodes που είναι αυτή την στιγμή failed
status.
"""

@tool
def estimate_impact(node_id: str) -> Dict[str, object]:
    global WORLD_STATE
    node = WORLD_STATE["nodes"].get(node_id)
    if node is None:
        return{"Error": f"Unknown node_id: {node_id}"}
    return{
        "population_affected": node["population_affected"],
        "criticality": node["criticality"]
    }
"""
Εκτιμεί το impact που έχει ένα failed node.
Παίρνει τα IDs των nodes.
Επιστρέφει το population_affected και το criticality.
Αν δεν υπάρχει το node αυτό που ψάχνουμε επιστρέφει error.
"""

@tool
def assign_repair_crew(node_ids: List[str], crew_ids: List[str]) -> Dict[str,Any]:
    global WORLD_STATE
    assignments = {}
    failures = []
    total_time = 0
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

        base_time = 2
        if node["criticality"] == "High":
            base_time = 4
        elif node["criticality"] == "Medium":
            base_time = 3
        total_time += base_time
    
    return{
        "assignments": assignments, 
        "total_estimated_time": total_time,
        "failures": failures
    }
"""
Ορίζει repair crews σε failed nodes και ενημερώνει την global μεταβλητη WORLD_STATE.
Η συνάρτηση παίρνει τα IDs των nodes και των repair crews.
Επιστρέφει τα IDs των nodes που έγιναν assigned στο αντιστοιχο repair crew,
το συνολικό estimated_time και τα failures.
"""