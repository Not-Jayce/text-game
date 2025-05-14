import json
import threading, time
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional

from utils.llm_client import LLMClient
from utils.screen import Screen
from support.gamestate import GameState
from support.home_base import home_base_screen

# Configure logging
log_folder = 'logs'
os.makedirs(log_folder, exist_ok=True)
log_filename = os.path.join(log_folder, f"game_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
logging.basicConfig(
    filename=log_filename,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Logging initialized.")

class Game(BaseModel):
    screen: Screen = Field(...)
    game_state: GameState = Field(...)

    @classmethod
    def create(cls, screen: Screen, game_state: Optional[GameState] = None):
        api_key = os.getenv("API_KEY")
        api_url = os.getenv("API_URL")
        llm_client = LLMClient.create(api_url, api_key, screen, None)

        if game_state is None:
            while True:
                screen.display_options("Choose the theme for this game", ["Space Exploration", "Dungeon Crawl", "Fantasy", "Wild West", "Custom"])
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

            game_state = GameState.create(llm_client, theme)
        game_state.llm_client.set_theme(game_state.theme)

        return cls(
            screen=screen,
            game_state=game_state
        )

    @classmethod
    def load(cls, screen: Screen, filename):
        logging.info(f"Loading game from {filename}")
        try:
            with open(filename, 'rb') as f:
                game_state = GameState.load(screen, f.read())
                return cls.create(screen, game_state)
        except FileNotFoundError:
            screen.display("Error loading game: Save file not found.")
            logging.error(f"Error loading game: Save file not found.")
            time.sleep(2)
            return None
        except Exception as e:
            screen.display(f"Error loading game: {e}")
            logging.error(f"Error loading game: {e}")
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
            try:
                self.save()
                logging.info("Autosave completed successfully.")
            except Exception as e:
                logging.error(f"Error during autosave: {e}")
            time.sleep(60)

    def save(self):
        self.game_state.save()


def main_menu(screen: Screen):
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
            game = Game.create(screen)
            if game:
                break
        elif c == ord('2') and save_exists:
            # Load the game state from a file
            screen.display("Loading game...")
            game = Game.load(screen, 'save.dat')
            if game:
                break

    return game
    

def main():
    load_dotenv("local.env")
    screen = Screen.create(width=70)

    game = main_menu(screen)
    game.run()


if __name__ == "__main__":
    main()