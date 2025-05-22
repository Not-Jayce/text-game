from numpy.random import choice as np_choice
from typing import TYPE_CHECKING, Sequence, TypeVar, Optional
import os, re

if TYPE_CHECKING:
    from utils.screen import Screen

T = TypeVar('T')


def choice(choices: Sequence[T], weights:Optional[list[float]] = None) -> T:
    """
    Selects a random choice from a list of choices based on given weights.
    
    :param choices: List of choices to select from.
    :param weights: List of weights corresponding to each choice. If None, all choices are equally likely.
    :return: A randomly selected choice from the list, based on weighting if provided.
    """
    if weights is None:
        weights = [1/len(choices)] * len(choices)

    rand_index = np_choice(list(range(len(choices))), p=weights)

    return choices[rand_index]


def file_browser(screen: "Screen", mode: str = "open"):
    """
    Opens a file browser to select or save .dat files.

    :param screen: The screen object to display the file browser.
    :param mode: The mode of operation, either "open" or "save".
    :return: The selected filename or None if cancelled.
    """

    files = [f for f in os.listdir('.') if f.endswith('.dat')]
    # Only allow alphanumerics, dash, underscore, and space (no tabs or other whitespace)
    valid_filename_re = re.compile(r'^[A-Za-z0-9\-_ ]+$')

    if mode == "open":
        if not files:
            screen.temp_display(2, "No .dat save files found.")
            return None
        while True:
            screen.display_options("Select a .dat file to load:", files)
            screen.add_new_line(f"Enter 1-{len(files)} to select, or 'b' to cancel.")
            c = screen.handle_keypress(None)
            if c == ord('b'):
                return None
            idx = c - ord('1')
            if 0 <= idx < len(files):
                return files[idx]

    elif mode == "save":
        while True:
            filename = screen.get_input("Enter a name for your save file:", 50).strip()
            if not filename:
                screen.temp_display(2, "Filename cannot be empty.")
                continue
            if not valid_filename_re.fullmatch(filename):
                screen.temp_display(2, "Invalid filename. Use only letters, numbers, spaces, '-', and '_'.")
                continue
            if not filename.lower().endswith('.dat'):
                filename += '.dat'
            if os.path.exists(filename):
                while True:
                    screen.display("File already exists. Overwrite? Press 'y' to confirm, 'b' to cancel.")
                    c = screen.handle_keypress(None)
                    if c == ord('y'):
                        return filename
                    elif c == ord('b'):
                        break
            else:
                return filename
    return None