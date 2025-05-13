from pydantic import BaseModel, Field
from typing import List, Optional
import pickle

from support.region import Region
from support.character import Character
from utils.llm_client import LLMClient

class GameState(BaseModel):
    llm_client: LLMClient = Field(...)
    theme: str = Field(...)
    currency: int = Field(10)
    currency_name: str = Field("currency")
    recruitment_cost: int = Field(10)
    characters: List[Character] = Field(default_factory=list)
    regions: List[Region] = Field(default_factory=list)
    current_region: Optional[Region] = Field(None)

    @classmethod
    def create(cls, llm_client: LLMClient, theme: str):
        llm_client.set_theme(theme)
        currency_name = llm_client.custom_generate(f"Create a unique name for a currency in a {theme} setting.\
                                                   Reply with just the name and no additional formatting.",
                                                   max_tokens=5, load_desc="Generating currency name")
        
        character_names = llm_client.multi_generate(3, "name", "character", "Generating character names", max_tokens=20)
        character_descriptions = llm_client.multi_generate(3, "description", "character", "Generating character descriptions",
                                                           name=character_names, max_tokens=100)
        
        region_names = llm_client.multi_generate(5, "name", "region", "Generating region names", max_tokens=20)
        region_descriptions = llm_client.multi_generate(5, "description", "region", "Generating region descriptions",
                                                       name=region_names, max_tokens=100)

        characters = [Character.create(llm_client, character_names[i], character_descriptions[i]) for i in range(3)]
        regions = [Region.create(llm_client, region_names[i], region_descriptions[i]) for i in range(5)]
        for region in regions:
            region.generate_locations(llm_client)

        return cls(
            llm_client=llm_client,
            characters=characters,
            regions=regions,
            current_region=None,
            theme=theme,
            currency_name=currency_name,
        )

    @classmethod
    def load(cls, llm_client: LLMClient, data):
        game_state = cls.create(llm_client, llm_client.theme)
        game_state_data = pickle.loads(data)
        for key, value in game_state_data.items():
            setattr(game_state, key, value)
        return game_state
    
    def save(self):
        with open('save.dat', 'wb') as f:
            f.write(self.model_dump()) #pickle.dumps

    def set_theme(self, theme: str):
        self.theme = theme
        self.llm_client.set_theme(theme)