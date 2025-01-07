import os
from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments


class IntentService:
    def __init__(self):
        pass

    async def determine_intent(self, kernel: Kernel, query):
        pluginsloc = os.path.join(os.getcwd(), "src", "plugins")
        category_plugin=kernel.add_plugin(parent_directory=pluginsloc, plugin_name="CategoryPlugin")        
        category_intent = await kernel.invoke(category_plugin["CategoryDetector"], KernelArguments(input=query))
        return category_intent.value[0].content
