from utils.base_utils import handle_keypress
from support.character import recruit_screen, view_characters_screen
from support.explore import explore_screen

def home_base_screen(stdscr, game_state):
    stdscr.clear()
    stdscr.addstr(0,0, f"Home Base (Currency: {game_state.currency})")
    stdscr.addstr(1,0, "Options:")
    stdscr.addstr(2,0, "1. Explore")
    stdscr.addstr(3,0, f"2. Recruit ({game_state.recruitment_cost} currency)")
    stdscr.addstr(4,0, "3. View Characters")
    stdscr.refresh()

    c = handle_keypress(stdscr, game_state)
    if c == ord('1'):
        explore_screen(stdscr, game_state)
    elif c == ord('2'):
        recruit_screen(stdscr, game_state)
    elif c == ord('3'):
        view_characters_screen(stdscr, game_state)