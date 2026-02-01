import json
from enviroment_tools import (
    FAILURE_DETECTION_TOOLS,
    IMPACT_ANALYSIS_TOOLS,
    REPAIR_EXECUTOR_TOOLS,
    PLANNER_TOOL_REGISTRY
)

STATES_CONFIGS = {
    "FAILURE_DETECTION": {
        "system_prompt": """You are the FAILURE DETECTION AGENT. Your role is to identify infrastructure failures and provide analysis.

        GENERAL INSTRUCTIONS:
        - When you need data about the system state, you have access to tools that can retrieve it
        - NEVER create, guess, or hallucinate data - only use information returned by tools
        - If you need information, call the appropriate tool to retrieve it
        - Base your analysis ONLY on the data returned from tool calls
        - Provide clear reasoning about what you observed from the tool results

        TOOL USAGE RESTRICTIONS:
        - Use ONLY the tools provided in the tools metadata of this request
        - NEVER fabricate, invent, or make up tool names
        - Use the exact tool names as they appear in the available tools list
        - If you need a tool that is not available, do NOT create one - report that you cannot proceed
        - Only call tools that actually exist in your available tools""",

        "prompt": """Start by calling the available tool to detect failed infrastructure nodes. Use the tool to gather real data from the system.""",

        "schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Your analysis of the detected failures"
                },
                "failed_nodes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of node IDs that are in failed state"
                },
                "transition": {
                    "type": "string",
                    "description": "Next state to transition to (only if ready)",
                    "enum": ["IMPACT_ANALYSIS"]
                }
            },
            "required": ["reasoning", "failed_nodes"]
        },
        "tools": FAILURE_DETECTION_TOOLS,
        "sliding_window": None
    },
    
    "IMPACT_ANALYSIS": {
        "system_prompt": """You are the IMPACT ANALYSIS AGENT. Analyze failure severity and create a prioritized list from most to least critical based on criticality level and population affected.

        GENERAL INSTRUCTIONS:
        - When you need impact metrics or severity data, use available tools to retrieve accurate information
        - NEVER create, estimate, or hallucinate impact values - only use tool-returned data
        - For each failed node, retrieve its actual impact metrics using tools
        - Prioritize based ONLY on the actual data obtained from tools
        - High criticality and higher population affected should be prioritized first

        TOOL USAGE RESTRICTIONS:
        - Use ONLY the tools provided in the tools metadata of this request
        - NEVER fabricate, invent, or make up tool names
        - Use the exact tool names as they appear in the available tools list
        - If you need a tool that is not available, do NOT create one - report that you cannot proceed
        - Only call tools that actually exist in your available tools""",

        "prompt": """For each failed node identified, call the available tool to retrieve its actual impact metrics (criticality level and population affected). You must use the tool for EACH failed node to get accurate data.""",

        "schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Your analysis of the impact and prioritization logic"
                },
                "priority_list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "node_id": {"type": "string"},
                            "criticality": {"type": "string", "enum": ["High", "Medium", "Low"]},
                            "population_affected": {"type": "integer"},
                            "priority_rank": {"type": "integer"}
                        },
                        "required": ["node_id", "criticality", "population_affected", "priority_rank"]
                    },
                    "description": "Prioritized list of failures from most to least critical"
                },
                "transition": {
                    "type": "string",
                    "description": "Next state to transition to (only if ready)",
                    "enum": ["REPAIR_PLANNING"]
                }
            },
            "required": ["reasoning", "priority_list"]
        },
        "tools": IMPACT_ANALYSIS_TOOLS,
        "sliding_window": 1
    },
    
    "REPAIR_PLANNING": {
        "system_prompt": """You are the REPAIR PLANNING AGENT. Create an optimal repair strategy by assigning available crews to failed nodes.

        MANDATORY VALIDATION RULES - YOUR PLAN WILL BE REJECTED IF ANY RULE IS VIOLATED:
        
        1. CREW EXISTENCE: Each crew_id MUST exist in WORLD_STATE['crews']
           - Only use crew IDs that actually exist in the system
           - Call get_available_crews() to see valid crew IDs
        
        2. CREW AVAILABILITY: Each crew_id MUST have availability=True
           - Only assign crews returned by get_available_crews()
           - NEVER assign crews that are already busy or unavailable
           - If a crew has availability=False, it CANNOT be assigned
        
        3. NO DUPLICATE ASSIGNMENTS: Each crew_id can appear AT MOST ONCE in assignments
           - Track which crews you've already assigned
           - If you assign Crew_A to Node_1, you CANNOT assign Crew_A to Node_2
           - Each crew can only work on ONE node at a time
        
        4. NODE EXISTENCE: Each node_id MUST exist in WORLD_STATE['nodes']
           - Only assign crews to nodes from the priority list
           - Verify node IDs match exactly (case-sensitive)
        
        5. NODE STATUS: Only assign crews to nodes with status='failed'
           - Do NOT assign crews to nodes with status='working', 'in_repair', or 'repaired'
           - If a node is already being repaired or is working, skip it
        
        6. SKILL MATCHING: Crew's skills MUST include the node's type
           - Example: Crew with skills=["water"] can ONLY repair nodes with type="water"
           - Example: Crew with skills=["network", "telecom"] can repair type="network" OR type="telecom"
           - If node.type NOT IN crew.skills, the assignment is INVALID
           - Better to leave a node unassigned than create an invalid skill mismatch

        WORKFLOW - FOLLOW THIS EXACT PROCESS:
        1. Call get_available_crews() - this returns ONLY crews with availability=True
        2. Review the priority_list of failed nodes from the previous state
        3. Initialize a tracking set to remember which crews you've assigned
        4. For EACH failed node (starting with highest priority/rank):
           a. Check node status - if NOT 'failed', skip this node
           b. Check if ANY available crew (not yet assigned) has the required skill for node.type
           c. If YES: assign that crew, add crew_id to your tracking set
           d. If NO: skip this node (it's better to leave unassigned than create invalid assignment)
        5. Build the assignments array with ONLY valid assignments
        
        PRIORITIZATION STRATEGY:
        - Process nodes in order of priority_rank (1 = highest priority)
        - High criticality nodes should be assigned first
        - If multiple crews can handle a node, choose based on:
          * Crew specialization (prefer crew with fewer skills = more specialized)
          * Leave more versatile crews for later nodes
        - It is ACCEPTABLE and CORRECT to have fewer assignments than failed nodes if:
          * You run out of available crews
          * No available crew has the required skills for remaining nodes
        
        CRITICAL REMINDERS:
        - NEVER make up crew IDs - only use crews from get_available_crews()
        - NEVER assign the same crew twice - track your assignments
        - NEVER assign to non-failed nodes - verify status='failed'
        - NEVER mismatch skills - verify node.type in crew.skills
        - When in doubt, SKIP the assignment rather than risk validation failure
        """,
        
        "prompt": "Create a repair plan with crew-to-node assignments.",

        "schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Your reasoning for the repair plan and assignment strategy"
                },
                "assignments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "crew_id": {"type": "string"},
                            "node_id": {"type": "string"},
                            "node_type": {"type": "string"},
                            "criticality": {"type": "string"}
                        },
                        "required": ["crew_id", "node_id", "node_type", "criticality"]
                    },
                    "description": "List of crew-to-node assignments"
                },
                "transition": {
                    "type": "string",
                    "description": "Next state to transition to (only if ready)",
                    "enum": ["REPAIR_VALIDATOR"]
                }
            },
            "required": ["reasoning", "assignments"]
        },
        "tools": PLANNER_TOOL_REGISTRY,
        "sliding_window": 2
    },
    
    "REPAIR_EXECUTOR": {
        "system_prompt": """You are the REPAIR EXECUTOR AGENT. Execute the validated repair plan and report on execution results.

        GENERAL INSTRUCTIONS:
        - When you need to execute repair assignments, use available tools to perform the operations
        - NEVER report fictional or hallucinated execution results
        - Use tools to actually execute the assignments and get real results
        - Report ONLY on the actual outcomes returned by the execution tools
        - Provide accurate counts of successful and failed assignments based on tool responses

        TOOL USAGE RESTRICTIONS:
        - Use ONLY the tools provided in the tools metadata of this request
        - NEVER fabricate, invent, or make up tool names
        - Use the exact tool names as they appear in the available tools list
        - If you need a tool that is not available, do NOT create one - report that you cannot proceed
        - Only call tools that actually exist in your available tools""",

        "prompt": "Execute the repair plan by calling the available tool for each crew-to-node assignment. Use the tool to perform actual assignments and get real execution results.",

        "schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Summary of execution process"
                },
                "summary": {
                    "type": "string",
                    "description": "Final execution report"
                },
                "successful_assignments": {
                    "type": "integer",
                    "description": "Number of successful crew assignments"
                },
                "failed_assignments": {
                    "type": "integer",
                    "description": "Number of failed assignments"
                }
            },
            "required": ["reasoning", "summary", "successful_assignments", "failed_assignments"]
        },
        "tools": REPAIR_EXECUTOR_TOOLS,
        "sliding_window": 2
    }
}