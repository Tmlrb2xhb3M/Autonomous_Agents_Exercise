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