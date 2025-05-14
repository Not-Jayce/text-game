from support.event import Event, event_screen
from support.gamestate import GameState
from utils.screen import Screen

def explore_screen(screen: Screen, game_state: GameState):
    while True:
        screen.display_options("Available Regions:", [region.name for region in game_state.regions])
        screen.add_new_line(f"Select a region to explore (1-{len(game_state.regions)}) or 'b' to return:")

        c = screen.handle_keypress(game_state)
        if c >= ord('1') and c <= ord(str(len(game_state.regions))):
            region_index = c - ord('1')
            game_state.current_region = game_state.regions[region_index]
            character_select_screen(screen, game_state)
        elif c == ord('b'):
            break


def character_select_screen(screen: Screen, game_state: GameState):
    selected_characters = []
    while True:
        screen.display(f"Exploring {game_state.current_region.name}",
                    game_state.current_region.description)
        
        screen.display_options(
            f"Select up to 3 characters to explore with (1-{len(game_state.characters)}) then 'enter' to continue or 'b' to return:",
            [character.name+(" (selected)"*(character in selected_characters)) for character in game_state.characters],
            clear=False, fromline = screen.get_line_count() + 1)

        c = screen.handle_keypress(game_state)

        if c >= ord('1') and c <= ord(str(len(game_state.characters))):
            character_index = c - ord('1')
            character = game_state.characters[character_index]
            if character in selected_characters:
                selected_characters.remove(character)
            elif len(selected_characters) < 3:
                selected_characters.append(character)

        elif c == ord('b'):
            explore = False
            break

        elif c == ord('\n'):
            explore = True
            break

    if explore:
        event = Event.create(game_state, game_state.current_region, selected_characters)
        event_screen(screen, event, game_state)