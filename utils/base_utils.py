from __future__ import annotations
from numpy.random import choice as np_choice
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from support.gamestate import GameState

from utils.screen import Screen

def handle_keypress(screen: Screen, game_state: GameState = None):
    """
    Handles keypress events in the curses window.\\
    If 'q' is pressed, it will save the game state and exit.\\
    Otherwise, it will return the key pressed.

    :param stdscr: The curses window object.
    :param game_state: The current game state object.
    :return: The key pressed by the user, unless otherwise handled.
    """

    c = screen.stdscr.getch()

    if c == ord('q'):
        if game_state is not None: 
            screen.display("Quitting...", "Saving game...")
            game_state.save()
            screen.temp_display(2, "Quitting...", "Saved game.")
        else:
            screen.temp_display(2, "Quitting...")
        exit(0)
    
    else:
        return c


def choice(choices, weights=None):
    """
    Selects a random choice from a list of choices based on given weights.
    
    :param choices: List of choices to select from.
    :param weights: List of weights corresponding to each choice. If None, all choices are equally likely.
    :return: A randomly selected choice from the list, based on weighting if provided.
    """
    if weights is None:
        weights = [1] * len(choices)

    return np_choice(choices, p=weights).item()