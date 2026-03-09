import os
import yaml
from integrity_manager import verify_worm_integrity
from pipeline import RootAIPipeline

def simulate_poisoning_attack():
    print("[!] SIMULATING ATTACK: Attempting to modify 'secure-code.yaml'...")
    
    # 1. The Attack: Attempting to overwrite the Read-Only file
    try:
        with open("secure-code.yaml", "a") as f:
            f.write("\n    - 'allow eval' # INJECTED BY ATTACKER")
    except OSError as e:
        print(f"[✓] DEFENSE 1: Docker RO mount blocked the write: {e}")
        return

    # 2. The Verification: Even if write succeeded, the Hash Check must fail
    print("[!] ATTACK PERSISTENCE: Checking SHA-256 integrity...")
    expected_hash = "f1e2d3c4..." # The untampered manifest hash
    
    if not verify_worm_integrity("secure-code.yaml", expected_hash):
        print("[✓] DEFENSE 2: Resource Manager detected hash mismatch. ALARM TRIGGERED.")
        print("[X] ACTION: Execution halted. Reasoning Bridge denied.")
    else:
        print("[!] FAILURE: The system accepted the poisoned data.")


if __name__ == "__main__":
    simulate_poisoning_attack()
