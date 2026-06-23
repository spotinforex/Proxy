
from agents.registration_agent import run_registration_agent

"""if __name__ == "__main__":
    

    scenarios = [
        {
            "label": "Registered business",
            "context": {
                "user_message": "I have not received my certificate",
                "owner_name": "Chukwuemeka Obi",
                "complaint_id": 1,
                "business_record": {
                    "business_name": "Sunshine Ventures",
                    "registration_number": "1234567",
                    "status": "registered",
                    "certificate_url": "./attachments/CERTIFICATE - SUNSHINE VENTURES.pdf",
                    "pending_reason": None,
                    "expected_date": None,
                }
            }
        },
        {
            "label": "Pending — missing documents",
            "context": {
                "user_message": "What is happening with my registration?",
                "owner_name": "Ngozi Eze",
                "complaint_id": 2,
                "business_record": {
                    "business_name": "Ngozi Fabrics",
                    "registration_number": "7654321",
                    "status": "pending",
                    "pending_reason": "missing documents",
                    "expected_date": None,
                    "certificate_url": None,
                }
            }
        },
        {
            "label": "Business not found",
            "context": {
                "user_message": "I registered last month and heard nothing",
                "owner_name": "Emeka Dike",
                "complaint_id": 3,
                "business_record": None
            }
        },
        {
            "label": "Pending — processing",
            "context": {
                "user_message": "When will my registration be ready?",
                "owner_name": "Adaeze Nwosu",
                "complaint_id": 4,
                "business_record": {
                    "business_name": "Adaeze Catering",
                    "registration_number": "9876543",
                    "status": "pending",
                    "pending_reason": "processing",
                    "expected_date": "2026-07-15",
                    "certificate_url": None,
                }
            }
        },
    ]

    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"Scenario: {scenario['label']}")
        print('='*60)
        result = run_registration_agent(scenario["context"])
        print(json.dumps(result, indent=2))
        """