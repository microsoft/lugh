import logging
import os
from semantic_kernel import Kernel
from semantic_kernel.utils.logging import setup_logging
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior

# doh?

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from plugins.lights_plugin import LightsPlugin
from dotenv import load_dotenv 

load_dotenv()

kernel = Kernel()

chat_completion = AzureChatCompletion(
    deployment_name=os.getenv("AZ_OPENAI_DEPLOYMENT"),
    api_key=os.getenv("AZ_OPENAI_ENDPOINT"),
    base_url=os.getenv("AZ_OPENAI_ENDPOINT"),
    service_id="mychat"
)
kernel.add_service(chat_completion)


# Set the logging level for  semantic_kernel.kernel to DEBUG.
setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

# 3 plugins?: classification, api call, rag, idk?
kernel.add_plugin('LightsPlugin', LightsPlugin)

execution_settings = AzureChatPromptExecutionSettings(tool_choice="auto")
execution_settings.function_call_behavior = FunctionCallBehavior.EnableFunctions(
    auto_invoke=True, filters={}
)


async def achat(chatHistory: ChatHistory) -> list[ChatMessageContent]:
    result = await chat_completion.get_chat_message_content(
        chat_history=chatHistory,
        settings=execution_settings,
        kernel=kernel
    )

    return result


__all__ = [achat]
