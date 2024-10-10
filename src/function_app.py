from azure.functions import func
from services.kernel_service import achat
import logging
from semantic_kernel.contents.chat_history import ChatHistory

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="initiate_orchestration")
async def initiate_orchestration(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    user_query = req.params.get("query")
    if not user_query:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            user_query = req_body.get("query")

    chatHistory = ChatHistory()
    chatHistory.add_message(user_query)

    resp = await achat(chatHistory)

    if user_query:
        return func.HttpResponse(resp[-1].inner_content, status_code=200)
    else:
        return func.HttpResponse(
            "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
            status_code=200,
        )
