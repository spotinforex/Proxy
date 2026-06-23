

import json

from agents.triage_agent import run_triage_agent

# ── Manual Test ───────────────────────────────────────────────────────────────

"""if __name__ == "__main__":

    test_messages = [
        "I have not received my certificate for Sunshine Ventures. My name is Chukwuemeka Obi.",
        "What is happening with my registration? My reg number is 1234567.",
        "My name is Ngozi Eze. I registered Ngozi Fabrics but haven't heard anything.",
        "Hello I need help",
        "I have not received my certificate",  # missing owner name
    ]

    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"Message: {msg}")
        print('='*60)
        result = run_triage_agent(msg)
        print(json.dumps(result, indent=2))
        """