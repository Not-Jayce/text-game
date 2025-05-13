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

    def generate_locations(self, llm_client: LLMClient):
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

    @classmethod
    def create(cls, llm_client: LLMClient, name: Optional[str] = None, description: Optional[str] = None):
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