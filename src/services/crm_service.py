class CrmService:
    def __init__(self):
        # This is a sample data that would be returned from a CRM system. Just a placeholder, add actual calls to CRM here
        self.sample_data = [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "crm": {
                    "plan": {
                        "PlanID": "123456789",
                        "PlanName": "Premium Health Plan",
                        "PlanType": "PHP",
                        "PlanStatus": "ACTIVE",
                        "PlanSystemTypeID": "COSMOS",
                        "BenefitPlanID": "123456789_PHP",
                        "DateOfService": "20241001",
                    }
                },
            }
        ]

    def get_sample_data(self):
        return self.sample_data[0]
    
