import random
import curses
from typing import Optional, List
from pydantic import BaseModel, Field

from support.gamestate import GameState
from support.region import Region
from support.character import Character
from utils.base_utils import choice
from utils.screen import Screen

class Event(BaseModel):
    type: str = Field(...)
    prompt: str = Field(...)
    description: str = Field(...)
    outcome: Optional[str] = Field(None)

    @classmethod
    def create(cls, game_state: GameState, region: Region, characters: List[Character]):
        event_type = choice(["combat", "exploration", "interaction"])
        description, prompt = game_state.llm_client.generate("event", return_prompt=True, subject_type=event_type,
                                                  region=region.name, characters=', '.join([char.name for char in characters]), load_desc="Generating event", max_tokens=400)
        return cls(type=event_type, prompt=prompt, description=description, outcome=None)

    def resolve(self, game_state: GameState):
        outcome = game_state.llm_client.generate("outcome", prompt=self.prompt, description=self.description,
                                                 outcome="Success with no injuries", load_desc="Generating outcome")
        self.outcome = outcome
        return self.outcome


def event_screen(screen: Screen, event: Event, game_state: GameState):
    screen.display_options(event.description, ["Engage", "Flee"])

    while True:
        c = screen.handle_keypress(game_state)
        if c == ord('1'):
            outcome = event.resolve(game_state)
            screen.display(outcome)
            break
        elif c == ord('2'):
            screen.display("You chose to flee.")
            break