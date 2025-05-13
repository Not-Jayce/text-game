import random
from pydantic import BaseModel, Field
from typing import List

from support.location import Location

class Region(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    hazard_level: int = Field(...)
    locations: List[str] = Field(default_factory=list)

    def add_location(self, location: str):
        self.locations.append(location)

    @classmethod
    def create(cls, llm_client):
        return cls(
            name=llm_client.generate_name("region"),
            description=llm_client.generate_description("region", llm_client.generate_name("region")),
            hazard_level=random.randint(0, 4),
            locations=[Location.create(llm_client, cls, i+1) for i in range(random.randint(1, 3))],
        )