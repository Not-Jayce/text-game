import json
import threading, time
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional

from utils.llm_client import LLMClient
from utils.screen import Screen
from support.gamestate import GameState
from support.home_base import home_base_screen

class Game(BaseModel):
    screen: Screen = Field(...)
    game_state: GameState = Field(...)

    @classmethod
    def create(cls, screen: Screen, llm_client: LLMClient, game_state: Optional[GameState] = None):
        if game_state is None:
            while True:
                screen.display_options("Choose the theme for this game", ["Sci-fi", "Dungeon Crawl", "Fantasy", "Wild West", "Custom"])
                c = screen.handle_keypress(game_state)
                if c == ord('1'):
                    theme = "sci-fi"
                    break
                elif c == ord('2'):
                    theme = "dungeon crawl"
                    break
                elif c == ord('3'):
                    theme = "fantasy"
                    break
                elif c == ord('4'):
                    theme = "wild west"
                    break
                elif c == ord('5'):
                    theme = screen.get_input("Enter a custom theme (Max. 50 characters; may produce unpredictable outputs)", 50)
                    break

            llm_client.set_theme(theme)
            game_state = GameState.create(llm_client, theme)

        return cls(
            screen=screen,
            llm_client=llm_client,
            game_state=game_state
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
            home_base_screen(self.screen, self.game_state)

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

        c = screen.handle_keypress(None)
        if c == ord('1'):
            # Create a new game
            screen.display("Creating new game...")
            game = Game.create(screen, llm_client)
            if game:
                break
        elif c == ord('2') and save_exists:
            # Load the game state from a file
            screen.display("Loading game...")
            game = Game.load(screen, llm_client, 'save.dat')
            if game:
                break

    return game
    

def main():
    load_dotenv("local.env")
    api_key = os.getenv("API_KEY")
    screen = Screen.create()
    llm_client = LLMClient.create(screen, "https://api.hyprlab.io/v1/chat/completions", api_key, None)

    game = main_menu(screen, llm_client)
    game.run()


if __name__ == "__main__":
    main()