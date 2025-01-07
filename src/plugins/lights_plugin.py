from typing import Annotated
from semantic_kernel.functions import kernel_function
from services.context_service import ContextService

class LightsPlugin:
    def __init__(self, context_service: ContextService):
        self.context_service = context_service

    lights = [
        {"id": 1, "name": "Table Lamp", "is_on": False},
        {"id": 2, "name": "Porch light", "is_on": False},
        {"id": 3, "name": "Chandelier", "is_on": True},
    ]

    @kernel_function(
        name="get_lights",
        description="Gets a list of lights and their current state",
    )
    def get_state(
        self,
    ) -> Annotated[str, "the output is a string"]:
        """Gets a list of lights and their current state."""
        return self.lights

    @kernel_function(
        name="change_state",
        description="Changes the state of the light",
    )
    def change_state(
        self,
        id: int,
        is_on: bool,
    ) -> Annotated[str, "the output is a string"]:
        """Changes the state of the light."""
        for light in self.lights:
            if light["id"] == id:
                light["is_on"] = is_on
                return light
        return None
    
    @kernel_function(
        name="increment_counter",
        description="Increments the counter",
    )
    def increment_counter(
        self
    ) -> Annotated[int, "the output is the new count"]:
        count = self.context_service.get_context("count")
        count += 1
        self.context_service.set_context("count", count)
        return count
    
    @kernel_function(
        name="get_counter",
        description="Gets the counter",
    )
    def get_counter(
        self
    ) -> Annotated[int, "the output is the current count"]:
        return self.context_service.get_context("count")
    

    