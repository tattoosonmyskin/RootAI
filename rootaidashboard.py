import json

class RootAIDashboard:
    @staticmethod
    def render_logic(plan: dict):
        """
        Visualizes the Reasoning Bridge synthesis for the Lead Architect.
        """
        print("\n" + "="*60)
        print(f" ROOTAI REASONING BRIDGE: {plan['intent'].upper()}")
        print("="*60)
        
        # Path A: Semantic Grounding
        print(f"\n[PATH A] SEMANTIC ROOTS (Meaning)")
        for root, concepts in plan['semantic_roots'].items():
            print(f" └─ Root: {root} -> Concepts: {', '.join(concepts)}")
            
        # Path B: Resource Manager (Constraints)
        print(f"\n[PATH B] WORM CONSTRAINTS (Logic)")
        for constraint in plan['hard_constraints']:
            print(f" └─ MANDATORY: {constraint}")
            
        print("-" * 60)
        
        # Validation Layer
        print(f"RELIABILITY SCORE: {plan['reliability']*100:.0f}%")
        print(f"HALLUCINATION RISK: {plan['hallucination_risk'].upper()}")
        
        if plan['reliability'] < 0.7:
            print("\n[!] WARNING: Grounding data is insufficient. Verification suggested.")
        
        print("="*60 + "\n")


if __name__ == "__main__":
    # Integration Example
    example_plan = {
        "intent": "Create an auth session with JWT",
        "semantic_roots": {"auth": ["identity", "token"], "session": ["state", "persistence"]},
        "hard_constraints": ["no eval", "JWT auth", "prepared statements"],
        "reliability": 0.75,
        "hallucination_risk": "low"
    }
    dashboard = RootAIDashboard()
    dashboard.render_logic(example_plan)
