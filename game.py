import json
import threading, time
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional

from utils.llm_client import LLMClient
from utils.base_utils import handle_keypress
from utils.screen import Screen
from support.gamestate import GameState

class Game(BaseModel):
    screen: Screen = Field(...)
    llm_client: LLMClient = Field(...)
    game_state: GameState = Field(...)

    @classmethod
    def create(cls, screen: Screen, llm_client: LLMClient, game_state: Optional[GameState] = None):
        if game_state is None:
            while True:
                screen.display_options("Choose the theme for this game", ["Sci-fi", "Dungeon Crawl", "Fantasy", "Wild West", "Custom"])
                c = handle_keypress(screen, None)
                match c:
                    case ord('1'):
                        theme = "sci-fi"
                        break
                    case ord('2'):
                        theme = "dungeon crawl"
                        break
                    case ord('3'):
                        theme = "fantasy"
                        break
                    case ord('4'):
                        theme = "wild west"
                        break
                    case ord('5'):
                        theme = screen.get_input("Enter a custom theme (may produce unpredictable outputs)")
                        break

            llm_client.set_theme(theme)
        return cls(
            screen=screen,
            llm_client=llm_client,
            game_state=game_state if game_state is not None else GameState.create(llm_client, theme)
        )

    @classmethod
    def load(cls, screen: Screen, llm_client: LLMClient, filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                game_state = GameState.load(llm_client, data)
                return cls.create(screen, llm_client, game_state)
        except FileNotFoundError:
            screen.display("Error loading game: Save file not found.")
            time.sleep(2)
            return None
        except json.JSONDecodeError:
            screen.display("Error loading game: Invalid save file.")
            time.sleep(2)
            return None
        except Exception as e:
            screen.display(f"Error loading game: {e}")
            time.sleep(2)
            return None

    def run(self):
        autosave_thread = threading.Thread(target=self.autosave)
        autosave_thread.daemon = True
        autosave_thread.start()

        while True:
            self.game_state.home_base_screen()

    def autosave(self):
        while True:
            self.save()
            time.sleep(60)

    def save(self):
        self.game_state.save()


def main_menu(screen: Screen, llm_client: LLMClient):
    if os.path.exists('save.dat'):
        save_exists = True
    else:
        save_exists = False

    while True:
        screen.display_options("Main Menu", ["New Game", "Resume" if save_exists else ""])

        c = handle_keypress(screen, None)
        if c == ord('1'):
            # Create a new game
            screen.display("Creating new game...")
            game = Game.create(screen, llm_client)
            if game:
                break
        elif c == ord('2') and save_exists:
            # Load the game state from a file
            screen.display(screen, "Loading game...")
            game = Game.load(screen, llm_client, 'save.dat')
            if game:
                break

    return game
    

def main():
    load_dotenv("local.env")
    api_key = os.getenv("API_KEY")
    llm_client = LLMClient.create("https://api.hyprlab.io/v1/chat/completions", api_key, None)
    screen = Screen.create()

    game = main_menu(screen, llm_client)
    game.run()


if __name__ == "__main__":
    main()