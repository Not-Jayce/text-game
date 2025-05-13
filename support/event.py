import random
import curses
from typing import Optional, List
from pydantic import BaseModel, Field

from support.gamestate import GameState
from support.region import Region
from support.character import Character
from utils.base_utils import choice, handle_keypress
from utils.llm_client import LLMClient
from utils.screen import Screen

class Event(BaseModel):
    type: str = Field(...)
    prompt: str = Field(...)
    description: str = Field(...)
    outcome: Optional[str] = Field(None)

    @classmethod
    def create(cls, llm_client: LLMClient, region: Region, characters: List[Character]):
        event_type = choice(["combat", "exploration", "interaction"])
        prompt = f"In the region of {region.name}, {', '.join([character.name for character in characters])} encounter a(n) {event_type} event"
        description = llm_client.generate_text(prompt)
        return cls(type=event_type, prompt=prompt, description=description, outcome=None)

    def resolve(self, game_state: GameState):
        outcome = game_state.llm_client.generate_outcome(self.prompt, self.description, "Victory with no injuries")
        setattr(self, "outcome", outcome)
        return self.outcome


def event_screen(screen: Screen, event: Event, game_state: GameState):
    screen.display_options(event.description, ["Engage", "Flee"])

    while True:
        c = handle_keypress(screen)
        if c == ord('1'):
            outcome = event.resolve(game_state)
            screen.display(outcome)
            break
        elif c == ord('2'):
            screen.display("You chose to flee.")
            break