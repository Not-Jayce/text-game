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
        return cls(
            llm_client=llm_client,
            characters=[Character.create(llm_client) for _ in range(3)],
            regions=[Region.create(llm_client) for _ in range(5)],
            current_region=None,
            theme=theme
        )

    @classmethod
    def load(cls, llm_client: LLMClient, data):
        game_state = cls.create(llm_client)
        game_state_data = pickle.loads(data)
        for key, value in game_state_data.items():
            setattr(game_state, key, value)
        return game_state
    
    def save(self):
        with open('save.dat', 'wb') as f:
            f.write(pickle.dumps(self.model_dump()))

    def set_theme(self, theme: str):
        self.theme = theme
        self.llm_client.set_theme(theme)
        for character in self.characters:
            character.specialization = theme
            character.description = self.llm_client.generate_description("character", character.name)