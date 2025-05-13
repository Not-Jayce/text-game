from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from support.region import Region
from utils.base_utils import choice


class Location(BaseModel):
    name: str = Field(...)
    region: Region = Field(...)
    distance: float = Field(...)
    description: str = Field(...)
    discovered: bool = Field(...)

    @classmethod
    def create(cls, llm_client, region: Region, distance: float):
        name = llm_client.generate_name(f"location in {region.name}")
        description = llm_client.generate_description(f"location in {region.name}", name)
        discovered = choice([True, False], weights=[0.7, 0.3])

        return cls(name=name, region=region, distance=distance, description=description, discovered=discovered)