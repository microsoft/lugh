from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions
from azure.identity import DefaultAzureCredential
from azure.cosmos.aio import ContainerProxy, DatabaseProxy
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent


# could potentially clean up this pattern to be more DRY but out of scope this late in the game
class ChatHistoryCosmosService:
    def __init__(
        self, endpoint: str, db_name: str, container_name: str, key: str = None
    ):
        if key is None or key.strip() == "":
            credential = DefaultAzureCredential()
            self.cosmos_client = CosmosClient(endpoint, credential=credential)
        else:
            self.cosmos_client = CosmosClient(endpoint, credential=key)
        self.db_name = db_name
        self.container_name = container_name

    async def __get_or_create_db__(self, database_name: str) -> DatabaseProxy:
        try:
            database_obj = self.cosmos_client.get_database_client(database_name)
            await database_obj.read()
            return database_obj
        except exceptions.CosmosResourceNotFoundError:
            print("Creating database")
        return await self.cosmos_client.create_database(database_name)

    async def __get_or_create_container__(
        self, database_obj: DatabaseProxy, container_name: str
    ) -> ContainerProxy:
        try:
            todo_items_container = database_obj.get_container_client(container_name)
            await todo_items_container.read()
            return todo_items_container
        except exceptions.CosmosResourceNotFoundError:
            print("Creating container with lastName as partition key")
            return await database_obj.create_container(
                id=container_name,
                partition_key=PartitionKey(path="/lastName"),
                offer_throughput=400,
            )
        except exceptions.CosmosHttpResponseError:
            raise

    async def aget_chat_history(self, call_agent: str, call_id: str) -> ChatHistory:
        db = await self.__get_or_create_db__(self.db_name)
        container = await self.__get_or_create_container__(db, self.container_name)
        query = f"SELECT VALUE c.chat FROM c WHERE c.PartitionKey = @partition_key AND c.id = @id"
        parameters = [
            {"name": "@partition_key", "value": call_agent},
            {"name": "@id", "value": call_id},
        ]

        items = [
            x async for x in container.query_items(query=query, parameters=parameters)
        ]

        if not items:
            return None

        # how to convert items to ChatHistory object
        chat = ChatHistory()

        ChatMessageContent(
            role=AuthorRole.SYSTEM,
            content="Welcome to the chat",
        )

        tool_calls = [m["tool_calls"] for m in items[0] if "tool_calls" in m]
        tool_call_map = [
            {"id": item["id"], "name": item["function"]["name"]}
            for sublist in tool_calls
            for item in sublist
        ]

        # tool_calls = [m for m in items[0] if "tool_calls" in m]
        for msg in items[0]:
            if msg["role"] == "system":
                chat.add_system_message(msg["content"])
            elif msg["role"] == "user":
                chat.add_user_message(msg["content"])
            elif msg["role"] == "assistant":
                if "content" in msg:
                    chat.add_assistant_message(msg["content"])
                elif "tool_calls" in msg:
                    chat.add_message(
                        ChatMessageContent(
                            role=AuthorRole.ASSISTANT,
                            items=[
                                FunctionCallContent(
                                    name=func_call["function"]["name"],
                                    id=func_call["id"],
                                    arguments=func_call["function"]["arguments"],
                                )
                                for func_call in msg["tool_calls"]
                            ],
                        )
                    )
            elif msg["role"] == "tool":
                if "tool_call_id" in msg:
                    chat.add_message(
                        ChatMessageContent(
                            role=AuthorRole.TOOL,
                            items=[
                                FunctionResultContent(
                                    # find the name from the FunctionCallContent using the id
                                    name=next(
                                        (
                                            record["name"]
                                            for record in tool_call_map
                                            if record["id"] == msg["tool_call_id"]
                                        ),
                                        None,
                                    ),
                                    id=msg["tool_call_id"],
                                    result=msg["content"],
                                )
                            ],
                        )
                    )
                elif "content" in msg:
                    chat.add_tool_message(msg["content"])
            else:
                print(f"skipped {msg} as it is an unhandled role")

        # https://github.com/microsoft/semantic-kernel/issues/7903
        # return ChatHistory.restore_chat_history(json_chat)
        return chat

    async def asave_chat_history(
        self, call_agent: str, call_id: str, chat_history
    ) -> bool:
        db = await self.__get_or_create_db__(self.db_name)
        container = await self.__get_or_create_container__(db, self.container_name)

        # https://github.com/microsoft/semantic-kernel/issues/7903
        chat = [
            msg.to_dict() for msg in chat_history.messages
        ]  # chat_history.serialize()

        return await container.upsert_item(
            body={"PartitionKey": call_agent, "id": call_id, "chat": chat}
        )
