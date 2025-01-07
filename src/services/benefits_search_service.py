# stubbed out - just returning the user query for now
# TODO ADD REAL IMPLEMENTATION OF API CALL TO BENEFITS SEARCH SERVICE

class BenefitsSearchService:
    def __init__(self):
        pass

    async def get_data(self, user_query, plan_type, plan_system_type_id, benefit_plan_id, date_of_service):
        response = f' in Benefits Search service with query: {user_query} | PlanType: {plan_type} | PlanSystemTypeID: {plan_system_type_id} | BenefitPlanID: {benefit_plan_id} | DateOfService: {date_of_service}'
        print(response)
        return response
