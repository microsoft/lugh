from semantic_kernel.contents.chat_history import ChatHistory
from config import AppConfig
from services.chat_history_cosmos_service import ChatHistoryCosmosService
from services.aisearch_service import AiSearchService
from services.benefits_search_service import BenefitsSearchService
from services.crm_service import CrmService
from services.intent_service import IntentService
from services.kernel_service import KernelService
from setup_logging import set_up_logging, set_up_metrics, set_up_tracing

config = AppConfig()

# setup SK logging, metrics, and tracing
set_up_logging(config=config)
set_up_tracing(config=config)
set_up_metrics(config=config)

# Configure OpenTelemetry to use Azure Monitor, this is the auto instrumentation
from azure.monitor.opentelemetry import configure_azure_monitor
configure_azure_monitor(connnection_string=config.app_insights_connstr)


# Create application instance
from flask import Flask, request

app = Flask(__name__)


@app.route("/", methods=["GET"])
def health_check():
    return "OK"


@app.route("/utterance", methods=["POST"])
async def receive_event_v2():
    sys_msg = f"""You are a silent observer in a phone conversation between a human health plan benefits assistant and a customer.
    In the conversation history provided to you, the USER is the customer, and the ASSISTANT is the human assistant.
    You are not allowed to interact with the customer USER directly, and you are not completing the conversation.
    Your purpose is to extract all searchable questions uttered by the customer USER, and the intent category for each, returing helpful information to be used by the human ASSISTANT as they continue to talk with the customer USER.
    If no well formed customer user question or need is found in the conversation, return only "no questions found".
    For each USER question or need identified, use the tools available to you to search for helpful information and determine intent for each identified question and then combine the results into a single response.
    In the "Information" returned, only include information retrieved from your tools; not from your general knowledge or from utterances in the conversation.
    If no supporting information is found for a user question with your tools, provide "none found" for the information related to that item.
    Always format your response like the examples below. 
    ###Example 1###
    No questions found
    ###Example 2###
    User question: How does the Monthly Challenge work?
    Information: [Details about monthly challenge from retrieve_kc_response function]
    Intent: General
    ###Example 3###
    User question: How much would a CGM cost?
    Information: [Details about CGM cost from retrieve_benefits_response function]
    Intent: Plan
    ###Example 4###
    User question: What is the best CGM for me?
    Information: none found
    Intent: General
    """

    call_agent = request.json["callAgent"]
    call_id = request.json["callId"]
    utterance = request.json["utterance"]
    speaker = request.json["speaker"]

    chat_history_service = ChatHistoryCosmosService(
        endpoint=config.db_endpoint,
        db_name=config.db_name,
        container_name=config.db_container,
        key=config.db_key,
    )

    chat_history = await chat_history_service.aget_chat_history(call_agent, call_id)

    if chat_history is None:
        chat_history = ChatHistory()
        chat_history.add_system_message(sys_msg)

    # consider some proompting to see if there is a question/intent etc without context first
    # to see if we should act on this in anyway...
    speaker = speaker.strip().lower()

    if speaker == "customer":
        chat_history.add_user_message(utterance)
    elif speaker == "advocate":
        chat_history.add_assistant_message(utterance)
        print("Bypassing AI processing for advocate utterance")
        return "No questions found"
    else:
        return 400, "Invalid speaker role"

    aisearch_service = AiSearchService()
    benefits_search_service = BenefitsSearchService()
    intent_service = IntentService()

    kernel = KernelService(
        deployment=config.ai_deployment,
        endpoint=config.ai_endpoint,
        api_version=config.ai_api_version,
        key=config.ai_api_key,
        aisearch_service=aisearch_service,
        benefits_search_service=benefits_search_service,
        intent_service=intent_service,
    )

    result = await kernel.achat(chat_history)

    chat_history.add_assistant_message(result.content)

    await chat_history_service.asave_chat_history(call_agent, call_id, chat_history)

    return result.content
