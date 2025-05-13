from pydantic import BaseModel, Field
from typing import Optional

from utils.base_utils import choice
from utils.llm_client import LLMClient


class Location(BaseModel):
    name: str = Field(...)
    region_name: str = Field(...)
    distance: float = Field(...)
    description: str = Field(...)
    discovered: bool = Field(...)

    @classmethod
    def create(cls, llm_client: LLMClient, region_name: str, distance: float, name: Optional[str] = None, description: Optional[str] = None):
        if name is None:
            name = llm_client.generate("name", f"location in {region_name}", "Generating locations", max_tokens=20)
        if description is None:
            description = llm_client.generate("description", f"location in {region_name}", "Generating locations", name=name, max_tokens=100)
        
        discovered = choice([True, False], weights=[0.67, 0.33])

        return cls(name=name, region_name=region_name, distance=distance, description=description, discovered=discovered)