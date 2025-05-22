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
            selected_region = game_state.regions[region_index]
            # Show region description and hazard level, ask for confirmation
            while True:
                screen.display(f"Exploring {selected_region.name}", f"{selected_region.description}", f"Hazard Level: {selected_region.hazard_level}")
                screen.add_new_line("Press 'y' to confirm, or 'b' to return to region selection.")
                confirm = screen.handle_keypress(game_state)
                if confirm == ord('y'):
                    game_state.current_region = selected_region
                    # Character selection before entering region
                    character_select_screen(screen, game_state)
                    break
                elif confirm == ord('b'):
                    break
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
            if len(selected_characters) == 0:
                screen.temp_display(2, "You must select at least one character to explore with.")
                continue
            explore = True
            break

    if explore:
        game_state.current_region.region_screen(screen, game_state)