from dotenv import load_dotenv
load_dotenv()

import json
from agent import InfrastructureRepairAgent
from world import WORLD_STATE

if __name__ == "__main__":
    agent = InfrastructureRepairAgent()
    
    result = agent.run(maxsteps=20)
    
    print("\n" + "="*70)
    print("FINAL WORLD STATE")
    print("="*70)
    print(json.dumps(WORLD_STATE, indent=2))
