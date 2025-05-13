from support.event import Event, event_screen
from support.gamestate import GameState

def explore_screen(stdscr, game_state):
    stdscr.clear()
    stdscr.addstr(0, 0, "Available Regions:")
    for i, region in enumerate(game_state.regions):
        stdscr.addstr(i + 1, 0, f"{i + 1}. {region.name}")
    stdscr.refresh()

    c = stdscr.getch()
    if c >= ord('1') and c <= ord(str(len(game_state.regions))):
        region_index = c - ord('1')
        game_state.current_region = game_state.regions[region_index]
        region_exploration_screen()


def region_exploration_screen(stdscr, game_state: GameState):
    stdscr.clear()
    stdscr.addstr(0, 0, f"Exploring {game_state.current_region.name}")
    stdscr.addstr(1, 0, game_state.current_region.description)
    stdscr.addstr(3, 0, "Characters:")
    for i, character in enumerate(game_state.characters):
        stdscr.addstr(i + 4, 0, f"{i + 1}. {character.name}")
    stdscr.addstr(len(game_state.characters) + 4, 0, "Select characters to bring:")
    stdscr.refresh()

    selected_characters = []
    while True:
        c = stdscr.getch()
        if c >= ord('1') and c <= ord(str(len(game_state.characters))):
            character_index = c - ord('1')
            if character_index in selected_characters:
                selected_characters.remove(character_index)
            else:
                selected_characters.append(character_index)
            stdscr.clear()
            stdscr.addstr(0, 0, f"Exploring {game_state.current_region.name}")
            stdscr.addstr(1, 0, game_state.current_region.description)
            stdscr.addstr(3, 0, "Characters:")
            for i, character in enumerate(game_state.characters):
                if i in selected_characters:
                    stdscr.addstr(i + 4, 0, f"{i + 1}. {character.name} (Selected)")
                else:
                    stdscr.addstr(i + 4, 0, f"{i + 1}. {character.name}")
            stdscr.addstr(len(game_state.characters) + 4, 0, "Press 'd' when done")
            stdscr.refresh()
        elif c == ord('d'):
            break

    characters_to_bring = [game_state.characters[i] for i in selected_characters]
    event = Event(game_state.llm_client, game_state.current_region, characters_to_bring)
    event_screen(event)