from utils.screen import Screen
from support.gamestate import GameState
from support.character import recruit_screen, view_characters_screen
from support.explore import explore_screen

def home_base_screen(screen: Screen, game_state: GameState):
    screen.display_options(f"Home Base (Currency: {game_state.currency} {game_state.currency_name})",
                           ["Explore", "Recruit", "View Characters"])

    c = screen.handle_keypress(game_state)
    if c == ord('1'):
        explore_screen(screen, game_state)
    elif c == ord('2'):
        recruit_screen(screen, game_state)
    elif c == ord('3'):
        view_characters_screen(screen, game_state)