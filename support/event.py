from typing import TYPE_CHECKING
import random
import curses
from typing import Optional, List
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from support.gamestate import GameState
    from support.region import Region
from support.character import Character
from utils.base_utils import choice
from utils.screen import Screen

class Event(BaseModel):
    type: str = Field(...)
    prompt: str = Field(...)
    onset_description: str = Field(...)
    outcome: str = Field("No outcome yet")
    outcome_desc: str = Field("No outcome yet")

    @classmethod
    def create(cls, game_state: "GameState", region: "Region", characters: List[Character]):
        event_type = choice(["combat", "exploration", "interaction"])
        onset_description, prompt = game_state.llm_client.generate_with_prompt("event", subject_type=event_type,
                                                  region=region.name, characters=', '.join([char.name for char in characters]), region_description=region.description, load_desc="Generating event", max_tokens=400)
        return cls(type=event_type, prompt=prompt, onset_description=onset_description, outcome="No outcome yet", outcome_desc="No outcome yet")

    def resolve(self, game_state: "GameState", user_choice: str):
        outcome: str = choice(["Success with no injuries", "Failure with no injuries", "Success with injuries", "Failure with injuries"])
        outcome_desc: str = game_state.llm_client.generate("outcome", prompt=self.prompt, description=self.onset_description,
                                                 choice=user_choice, outcome=outcome, load_desc="Generating outcome") 
        self.outcome = outcome
        self.outcome_desc = outcome_desc
        return self.outcome


def event_screen(screen: Screen, event: Event, game_state: "GameState"):
    options = ["Engage", "Talk", "Flee"]
    screen.display_options(event.onset_description, options)

    while True:
        c = screen.handle_keypress(game_state)
        idx = c - ord('1')
        if 0 <= idx < len(options):
            event.resolve(game_state, options[idx])
            screen.display(event.outcome_desc)
            screen.add_new_line("Press any key to continue...")
            screen.handle_keypress(game_state)
            break