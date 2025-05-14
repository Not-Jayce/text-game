import random
from pydantic import BaseModel, Field
from typing import List, Optional

from support.location import Location
from utils.llm_client import LLMClient

class Region(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    hazard_level: int = Field(...)
    locations: List[Location] = Field(default_factory=list)

    def create_locations(self, llm_client: LLMClient, locations: Optional[List[Location]] = None):
        """
        Creates locations for the region using the LLM client.
        If locations are provided, they will be used instead of generating new ones.

        :param llm_client: The LLM client to use for generating locations.
        :param locations: Optional list of locations to use instead of generating new ones.
        """
        if locations is None:
            num_locations = random.randint(2, 5)

            location_names = llm_client.multi_generate(num_locations, "name", f"location in {self.name} region",
                                                    "Generating location names", max_tokens=20)
            location_descriptions = llm_client.multi_generate(num_locations, "description", f"location in {self.name} region",
                                                            "Generating location descriptions",
                                                            name=location_names, max_tokens=100)
            try:
                self.locations = [Location.create(llm_client, self.name, i+1, location_names[i],
                                            location_descriptions[i]) for i in range(num_locations)]
            except IndexError:
                print("Error: Not enough location names or descriptions generated.")
                print(f"Generated names: {location_names}")
                print(f"Generated descriptions: {location_descriptions}")
        
        else:
            self.locations = locations

    @classmethod
    def create(cls, llm_client: LLMClient, name: Optional[str] = None, description: Optional[str] = None):
        """
        Creates a new region using the LLM client.
        If name and description are provided, they will be used instead of generating new ones.

        :param llm_client: The LLM client to use for generating the region.
        :param name: Optional name for the region.
        :param description: Optional description for the region.
        :return: A new Region instance.
        """
        if name is None:
            name = llm_client.generate("name", "region", "Generating regions", max_tokens=20)
        if description is None:
            description = llm_client.generate("description", "region", "Generating regions", name=name, max_tokens=100)
        return cls(
            name=name,
            description=description,
            hazard_level=random.randint(0, 4),
            locations=[],
        )