import os
import logging
from semantic_kernel import Kernel
from semantic_kernel.utils.logging import setup_logging
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from plugins.knowledge_plugin import KnowledgePlugin
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from azure.identity import DefaultAzureCredential

from services.aisearch_service import AiSearchService
from services.benefits_search_service import BenefitsSearchService
from services.intent_service import IntentService

default_credential = DefaultAzureCredential()


class KernelService:
    def __init__(
        self, deployment: str, endpoint: str, api_version: str, aisearch_service: AiSearchService, benefits_search_service: BenefitsSearchService, intent_service: IntentService, key: str = None
    ):
        self.kernel = Kernel()
        service_id = "azure_oai"
        if key is None or key.strip() == "":
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            self.chat_completion = AzureChatCompletion(
                service_id=service_id,
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=token.token,
                api_version=api_version,
            )
        else:
            self.chat_completion = AzureChatCompletion(
                service_id=service_id,
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=key,
                api_version=api_version,
            )
        self.kernel.add_service(self.chat_completion)

        # Set the logging level for  semantic_kernel.kernel to DEBUG.
        setup_logging()
        logging.getLogger("kernel").setLevel(logging.DEBUG)

        # Add a plugin (the LightsPlugin class is defined below)
        #self.kernel.add_plugin(LightsPlugin(context_service=context_service), "Lights")
        self.kernel.add_plugin(KnowledgePlugin(kernel=self.kernel, aisearch_service=aisearch_service, benefits_search_service=benefits_search_service, intent_service=intent_service), "KnowledgePlugin")
       
        # Add a prompt plugin from folder
        # plugins_directory = os.getcwd() + "\\src\\plugins"
        # plugin_directory = os.path.join(os.getcwd(), "src", "plugins")
        # self.kernel.add_plugin(parent_directory=plugin_directory, plugin_name="KnowledgePlugin")
        
        # todo: look at more sophisticated way to load plugins
        #   plugin_names = [
        #     plugin
        #     for plugin in os.listdir(plugins_directory)
        #     if os.path.isdir(os.path.join(plugins_directory, plugin))
        # ]
        # script_directory = os.path.dirname(__file__)
        # plugins_directory = os.path.join(script_directory, "plugins")

        # service_id = None

        # plugin_names = [
        #     plugin for plugin in os.listdir(plugins_directory) if os.path.isdir(os.path.join(plugins_directory, plugin))
        # ]

        # for each plugin, add the plugin to the kernel
        # try:
        #     for plugin_name in plugin_names:
        #         kernel.import_plugin_from_prompt_directory(
        #             plugins_directory, plugin_name
        #         )
        # except ValueError as e:
        #     logging.exception(f"Plugin {plugin_name} not found")

        # Enable planning
        self.execution_settings = AzureChatPromptExecutionSettings()
        self.execution_settings.function_choice_behavior = (
            FunctionChoiceBehavior.Auto()
        )  # filter out plugins that are not to be used automatically

    async def achat(self, chat_history: ChatHistory):
        result = await self.chat_completion.get_chat_message_content(
            chat_history=chat_history,
            settings=self.execution_settings,
            kernel=self.kernel,
        )

        return result
