from __future__ import annotations
from typing import TYPE_CHECKING
import time
from pydantic import BaseModel, Field
from typing import List, Optional

from utils.base_utils import choice
from utils.llm_client import LLMClient
from utils.screen import Screen

if TYPE_CHECKING:
    from support.gamestate import GameState

class Character(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    specialization: str = Field(...)
    talent: Optional[str] = Field(None)
    level: int = Field(1)
    xp: int = Field(0)
    hp: int = Field(1)
    gear: List[str] = Field(default_factory=list)

    def gain_xp(self, amount: int):
        self.xp += amount
        if self.xp >= self.level * 10:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.hp = self.level
        self.xp = 0

    @classmethod
    def create(cls, llm_client: LLMClient, name: Optional[str] = None, description: Optional[str] = None):
        if name is None:
            name = llm_client.generate("name","character", "Generating characters", max_tokens=20)
        if description is None:
            description = llm_client.generate("description", "character", "Generating characters", name=name, max_tokens=100)
            
        return cls(
            name=name,
            description=description,
            specialization=choice(["engineer", "scientist", "soldier"]),
            talent=choice(["polymath", "capable", "planner", None]),
            level=1,
            xp=0,
            hp=1,
            gear=[]
        )


def recruit_screen(screen: Screen, game_state: GameState):
    while True:
        screen.display_options(
            f"Would you like to recruit a new character? Cost: {game_state.recruitment_cost} {game_state.currency_name}",
            ["Yes", "No"])
        
        c = screen.handle_keypress(game_state)
        if c == ord('y') or c == ord('Y') or c == ord('1'):
            new_character = recruit_character(game_state)
            if new_character is not None:
                screen.display(f"Recruited {new_character.name} for {game_state.recruitment_cost} {game_state.currency_name}!")
                time.sleep(2)
            else:
                screen.display(f"Not enough {game_state.currency_name}.")
                time.sleep(2)
        elif c == ord('n') or c == ord('N') or c == ord('2'):
            break


def recruit_character(game_state: GameState):
    if game_state.currency >= game_state.recruitment_cost:
        new_character = Character.create(game_state.llm_client)
        game_state.characters.append(new_character)
        game_state.currency -= game_state.recruitment_cost
        game_state.recruitment_cost +=5
        return new_character
    else:
        return None


def view_characters_screen(screen: Screen, game_state: GameState):
    while True:
        screen.display_options(
            "Characters",
            [character.name for character in game_state.characters]
        )

        screen.add_new_line("Select a character to view details or 'b' to return to the home base.")

        c = screen.handle_keypress(game_state)
        if c == ord('b'):
            break
        elif c >= ord('1') and c <= ord(str(len(game_state.characters))):
            character_index = c - ord('1')
            full_character_screen(screen, game_state, game_state.characters[character_index])


def full_character_screen(screen: Screen, game_state: GameState, character: Character):
    screen.display(f"Name: {character.name}",
                   f"Description: {character.description}",
                   f"Specialization: {character.specialization}",
                   f"Talent: {character.talent if character.talent else 'None'}",
                   f"Level: {character.level}",
                   f"XP: {character.xp}/{character.level * 10}",
                   f"HP: {character.hp}/{character.level}",
                   f"Gear: {', '.join(character.gear) if character.gear else 'None'}",
                   "Press any key to return to character list.")
    
    screen.handle_keypress(game_state)