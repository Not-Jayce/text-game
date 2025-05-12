import curses, pickle, json
import threading, time
from llm_client import LLMClient
from character import Character
from region import Region
from event import Event

class GameState:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.currency =10
        self.recruitment_cost =10
        self.characters = [Character(llm_client) for _ in range(3)]
        self.regions = [Region(llm_client)]

    def recruit_character(self):
        if self.currency >= self.recruitment_cost:
            new_character = Character(self.llm_client)
            self.characters.append(new_character)
            self.currency -= self.recruitment_cost
            self.recruitment_cost +=5
            return new_character
        else:
            return None
    
    def save(self):
        return pickle.dumps(self.__dict__)

    @classmethod
    def load(cls, llm_client, data):
        game_state = cls(llm_client)
        game_state.__dict__.update(pickle.loads(data))
        return game_state

class Game:
    def __init__(self, stdscr, llm_client):
        self.stdscr = stdscr
        self.llm_client = llm_client
        self.game_state = GameState(llm_client)
        self.current_region = None

    def run(self):
        autosave_thread = threading.Thread(target=self.autosave)
        autosave_thread.daemon = True # So that the thread dies when the main thread dies
        autosave_thread.start()

        self.home_base_screen()
        self.save()

    def home_base_screen(self):
        self.stdscr.clear()
        self.stdscr.addstr(0,0, f"Home Base (Currency: {self.game_state.currency})")
        self.stdscr.addstr(1,0, "Options:")
        self.stdscr.addstr(2,0, "1. Explore")
        self.stdscr.addstr(3,0, f"2. Recruit ({self.game_state.recruitment_cost} currency)")
        self.stdscr.addstr(4,0, "3. View Characters")
        self.stdscr.refresh()

        c = self.stdscr.getch()
        if c == ord('1'):
            self.explore_screen()
        elif c == ord('2'):
            self.recruit_screen()
        elif c == ord('3'):
            self.view_characters_screen()

    def explore_screen(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Available Regions:")
        for i, region in enumerate(self.regions):
            self.stdscr.addstr(i + 1, 0, f"{i + 1}. {region.name}")
        self.stdscr.refresh()

        c = self.stdscr.getch()
        if c >= ord('1') and c <= ord(str(len(self.regions))):
            region_index = c - ord('1')
            self.current_region = self.regions[region_index]
            self.region_exploration_screen()

    def recruit_screen(self):
        new_character = self.game_state.recruit_character()
        if new_character is not None:
            self.stdscr.clear()
            self.stdscr.addstr(0,0, f"Recruited {new_character.name}!")
            self.stdscr.refresh()
            curses.napms(2000)
        else:
            self.stdscr.clear()
            self.stdscr.addstr(0,0, "Not enough currency!")
            self.stdscr.refresh()
            curses.napms(2000)

    def view_characters_screen(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, "Characters:")
        for i, character in enumerate(self.characters):
            self.stdscr.addstr(i + 1, 0, f"{i + 1}. {character.name} (Level {character.level})")
        self.stdscr.refresh()
        c = self.stdscr.getch()

    def region_exploration_screen(self):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, f"Exploring {self.current_region.name}")
        self.stdscr.addstr(1, 0, self.current_region.description)
        self.stdscr.addstr(3, 0, "Characters:")
        for i, character in enumerate(self.characters):
            self.stdscr.addstr(i + 4, 0, f"{i + 1}. {character.name}")
        self.stdscr.addstr(len(self.characters) + 4, 0, "Select characters to bring:")
        self.stdscr.refresh()

        selected_characters = []
        while True:
            c = self.stdscr.getch()
            if c >= ord('1') and c <= ord(str(len(self.characters))):
                character_index = c - ord('1')
                if character_index in selected_characters:
                    selected_characters.remove(character_index)
                else:
                    selected_characters.append(character_index)
                self.stdscr.clear()
                self.stdscr.addstr(0, 0, f"Exploring {self.current_region.name}")
                self.stdscr.addstr(1, 0, self.current_region.description)
                self.stdscr.addstr(3, 0, "Characters:")
                for i, character in enumerate(self.characters):
                    if i in selected_characters:
                        self.stdscr.addstr(i + 4, 0, f"{i + 1}. {character.name} (Selected)")
                    else:
                        self.stdscr.addstr(i + 4, 0, f"{i + 1}. {character.name}")
                self.stdscr.addstr(len(self.characters) + 4, 0, "Press 'd' to done")
                self.stdscr.refresh()
            elif c == ord('d'):
                break

        characters_to_bring = [self.characters[i] for i in selected_characters]
        event = Event(self.llm_client, self.current_region, characters_to_bring)
        self.event_screen(event)

    def event_screen(self, event):
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, event.description)
        self.stdscr.addstr(2, 0, "Options:")
        self.stdscr.addstr(3, 0, "1. Engage")
        self.stdscr.addstr(4, 0, "2. Flee")
        self.stdscr.refresh()

        c = self.stdscr.getch()
        if c == ord('1'):
            outcome = event.resolve(self.llm_client, [character for character in self.characters if character in [character for character in self.characters]])
            self.stdscr.clear()
            self.stdscr.addstr(0, 0, outcome)
            self.stdscr.refresh()
            curses.napms(4000)
        elif c == ord('2'):
            self.stdscr.clear()
            self.stdscr.addstr(0, 0, "You flee the scene.")
            self.stdscr.refresh()
            curses.napms(2000)

    def save(self):
        data = self.game_state.to_dict()
        with open('save.json', 'w') as f:
            json.dump(data, f)

    @classmethod
    def load(cls, stdscr, llm_client):
        try:
            with open('save.json', 'r') as f:
                data = json.load(f)
                game_state = GameState.from_dict(llm_client, data)
                game = cls(stdscr, llm_client)
                game.game_state = game_state
                return game
        except FileNotFoundError:
            return cls(stdscr, llm_client)
        
    def autosave(self):
        while True:
            self.save()
            time.sleep(60) # Save every minute
        
def main_menu(stdscr):
    stdscr.clear()
    stdscr.addstr(0,0, "Main Menu")
    stdscr.addstr(1,0, "1. New Game")
    stdscr.addstr(2,0, "2. Resume")
    stdscr.refresh()

    c = stdscr.getch()
    if c == ord('1'):
        return 'new_game'
    elif c == ord('2'):
        return 'resume'
    else:
        return main_menu(stdscr)

def main(stdscr):
    llm_client = LLMClient("https://api.hyprlab.com/v1/chat/completions", "API-KEY-HERE")

    while True:
        choice = main_menu(stdscr)
        if choice == 'new_game':
            game = Game(stdscr, llm_client)
            break
        elif choice == 'resume':
            # Load the game state from a file
            try:
                with open('save.dat', 'rb') as f:
                    game = Game(stdscr, llm_client)
                    game.game_state = GameState.load(llm_client, f.read())
                break
            except FileNotFoundError:
                game = Game(stdscr, llm_client)

    game.run()

curses.wrapper(main)