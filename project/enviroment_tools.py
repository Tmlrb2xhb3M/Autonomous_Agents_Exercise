from typing import Dict

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
def estimate_impact(node_id: str) -> Dict[str, object]:
    global WORLD_STATE
    node = WORLD_STATE["nodes"].get(node_id)
    if node is None:
        return{"Error": f"Unknown node_id: {node_id}"}
    return{
        "population_affected": node["population_affected"],
        "criticality": node["criticality"]
    }