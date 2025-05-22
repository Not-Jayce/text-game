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
from utils.base_utils import file_browser
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
    filename: Optional[str] = Field(None)

    @classmethod
    def create(cls, screen: Screen, game_state: Optional[GameState] = None, filename: Optional[str] = None):
        api_key = os.getenv("API_KEY")
        api_url = os.getenv("API_URL")
        if not api_key or not api_url:
            screen.temp_display(2, "Error: API key or URL not found in environment variables.")
            logging.error("Error: API key or URL not found in environment variables.")
            time.sleep(2)
            return None
        llm_client = LLMClient.create(api_url, api_key, screen, None)

        if game_state is None:
            while True:
                screen.display_options("Choose the theme for this game", ["Space Exploration", "Dungeon Crawl", "Fantasy", "Wild West", "Custom (Warning: May cause unpredictable output)"])
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
                    theme = screen.get_input("Enter a custom theme (Max. 50 characters)", 50)
                    break

            game_state = GameState.create(llm_client, theme)

        if game_state.llm_client:
            game_state.llm_client.set_theme(game_state.theme)

        return cls(
            screen=screen,
            game_state=game_state,
            filename=filename
        )

    @classmethod
    def load(cls, screen: Screen, filename):
        logging.info(f"Loading game from {filename}")
        try:
            with open(filename, 'rb') as f:
                game_state = GameState.load(screen, f.read())
                return cls.create(screen, game_state, filename)
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

    def save(self, filename: Optional[str] = None):
        self.game_state.save(filename)


def main_menu(screen: Screen):
    while True:
        screen.display_options("Main Menu", ["New Game", "Load Game"])
        c = screen.handle_keypress(None)
        if c == ord('1'):
            filename = file_browser(screen, mode="save")
            if filename:
                screen.display("Creating new game...")
                game = Game.create(screen, filename=filename)
                if game:
                    game.save(filename)
                    screen.temp_display(2, f"Game will be saved to {filename}")
                    break
        elif c == ord('2'):
            filename = file_browser(screen, mode="open")
            if filename:
                screen.display(f"Loading game from {filename}...")
                game = Game.load(screen, filename)
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