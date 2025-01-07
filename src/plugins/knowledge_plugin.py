from typing import Annotated
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from services.benefits_search_service import BenefitsSearchService
from services.aisearch_service import AiSearchService
from services.crm_service import CrmService
from services.intent_service import IntentService

import json
import os

class KnowledgePlugin:
    def __init__(self, kernel: Kernel, aisearch_service: AiSearchService, benefits_search_service: BenefitsSearchService, intent_service: IntentService):
        self.aisearch_service = aisearch_service
        self.benefits_search_service = benefits_search_service
        self.kernel = kernel
        self.intent_service = intent_service

    @kernel_function(
        name="retrieve_kc_response",
        description="To search general process and service information including eligibility criteria, regarding a single user_query identfied in a customer conversation",
    )
    async def retrieve_kc_response( 
        self,
        user_query:Annotated[str," A searchable need or question related to health care posed by the USER in the conversation"]
    ) -> Annotated[str, "the output is concatenated context of top 5 searches and the determined intent."]:
        #Get the raw vector for the given question
        #Invoke the AI search to get the Top5 results
        #Format the response and return the context
        determined_intent = await self.intent_service.determine_intent(self.kernel, user_query)
        aisearch_data = await self.aisearch_service.get_data(user_query)
        return {
                "intent": determined_intent,
                "aisearch_data": aisearch_data
            }
        
    @kernel_function(
        name="retrieve_benefits_response",
        description="To search both general process and service information as well as specific plan benefit information (examples: copay, deductible, payment, rewards, balances) regarding a single user_query identfied in a customer conversation for the given customer plan parameters",
    )
    async def retrieve_benefits_response( 
        self,
        user_query:Annotated[str," A searchable need or question related to health care posed by the USER in the conversation"]
    ) -> Annotated[str, "the output is the benefits api response for the given user_query and current plan details and the determined intent."]:
        
        determined_intent = await self.intent_service.determine_intent(self.kernel, user_query)
       
        # pull in crm payload example 
        crm_service = CrmService()
        crm_payload = crm_service.get_sample_data()
        plan_system_type_id = crm_payload["crm"]["plan"]["PlanSystemTypeID"]
        benefit_play_id = crm_payload["crm"]["plan"]["BenefitPlanID"]
        date_of_service = crm_payload["crm"]["plan"]["DateOfService"]
        plan_type = crm_payload["crm"]["plan"]["PlanType"]
        #search benefits service for specific benefit information
        aisearch_data = await self.aisearch_service.get_data(user_query)
        benefitsearch_data = await self.benefits_search_service.get_data(user_query, plan_type = plan_type, plan_system_type_id = plan_system_type_id, benefit_plan_id = benefit_play_id, date_of_service = date_of_service)
        return {
                "intent": determined_intent,
                "aisearch_data": aisearch_data,
                "benefitsearch_data": benefitsearch_data
            }
 