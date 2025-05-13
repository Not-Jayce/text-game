from pydantic import BaseModel, Field
from typing import List, Optional
import curses, time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from support.gamestate import GameState

class Screen(BaseModel):
    stdscr: curses.window = Field(...)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            curses.window: ""
        }

    @classmethod
    def create(cls):
        """
        Creates a new Screen instance.
        """
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        stdscr.keypad(True)
        return cls(stdscr=stdscr)

    def display(self, text: str, *args: List[str], fromline: int = 0, clear: bool = True):
        """
        Displays a simple text message on the screen.

        :param text: The text to display.
        :param fromline: The line number to start displaying the text from.
        :param args: Additional lines of text to display.
        """
        if clear:
            self.stdscr.clear()

        # Get each line of the text including any additional lines passed in args
        text_lines = text.split('\n')
        for arg in args:
            text_lines.extend(arg.split('\n'))

        for i, line in enumerate(text_lines):
            self.stdscr.addstr(i+fromline, 0, line)
        self.stdscr.refresh()

    def display_options(self, description: str = "", options: List[str] = [], fromline: int = 0, clear: bool = True):
        """
        Displays a list of options on the screen.

        :param description: The description to display at the top.
        :param options: A list of options to display.
        :param fromline: The line number to start displaying the options from.
        """
        line_modifier = fromline
        option_num = 1
        if clear:
            self.stdscr.clear()

        if description:
            desc_lines = description.split("\n")
            for desc_line in desc_lines:
                self.stdscr.addstr(line_modifier, 0, desc_line)
                line_modifier += 1
            
            line_modifier += 1
            self.stdscr.addstr(line_modifier, 0, "Options:")
            line_modifier += 1

        for _, option in enumerate(options):
            if option:
                option_list = option.split("\n")
                for j, opt in enumerate(option_list):
                    if j == 0:
                        self.stdscr.addstr(line_modifier, 0, f"{option_num}. {opt}")
                        line_modifier += 1
                        option_num += 1
                    else:
                        self.stdscr.addstr(line_modifier, 2, opt)
                        line_modifier += 1

        self.stdscr.refresh()

    def clear(self):
        """Clears the screen."""
        self.stdscr.clear()
        self.stdscr.refresh()

    def update_line(self, line: str, row: int):
        """
        Updates a single line of text in a specific row on the screen.

        :param line: The text to add.
        :param row: The row number to add the text to.
        """
        self.stdscr.addstr(row, 0, line)
        self.stdscr.refresh()

    def add_new_line(self, line: str, gap: int = 0):
        """
        Adds a new line of text to the next available row on the screen.

        :param line: The text to add.
        """
        y, x = self.stdscr.getyx()
        y += gap

        self.stdscr.addstr(y + 1, 0, line)
        self.stdscr.refresh()
    
    def temp_display(self, duration: int, text: str, *args: List[str]):
        """
        Temporarily displays a message on the screen for a specified duration then goes back to the previous display.

        :param duration: The duration in seconds to display the text.
        :param text: The text to display.
        :param args: Additional lines of text to display.
        """
        current_display = self.stdscr.instr(0, 0).decode('utf-8').strip()
        self.display(text, *args)

        time.sleep(duration)

        self.clear()
        self.stdscr.addstr(0, 0, current_display)

    def get_line_count(self) -> int:
        """
        Returns the number of lines currently displayed on the screen.

        :return: The number of lines displayed.
        """
        y, _ = self.stdscr.getyx()
        return y+1

    def handle_keypress(self, game_state: "GameState" = None):
        """
        Handles keypress events in the curses window.\\
        If 'q' is pressed, it will save the game state and exit.\\
        Otherwise, it will return the key pressed.

        :param stdscr: The curses window object.
        :param game_state: The current game state object.
        :return: The key pressed by the user, unless otherwise handled.
        """

        c = self.stdscr.getch()

        if c == ord('q'):
            if game_state is not None: 
                self.display("Quitting...", "Saving game...")
                game_state.save()
                self.temp_display(2, "Quitting...", "Saved game.")
            else:
                self.temp_display(2, "Quitting...")
            exit(0)
        
        else:
            return c

    def get_input(self, prompt: str, charlim: Optional[int] = None) -> str:
        """
        Displays a prompt and waits for user input.

        :param prompt: The prompt to display.
        :return: The user input.
        """
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, prompt)
        self.stdscr.addstr(1, 0, "Input: ")
        self.stdscr.refresh()
        user_input = ""
        while True:
            char = self.stdscr.get_wch()
            if char == '\n':  # Enter key
                break
            elif char == '\b':  # Backspace key
                if len(user_input) > 0:
                    user_input = user_input[:-1]
                    y, x = self.stdscr.getyx()
                    self.stdscr.addstr(y, x-1, " ")
                    if x == 0:
                        y -= 1
                        prev_line = self.stdscr.instr(y - 1, 0).decode('utf-8').rstrip()
                        x = len(prev_line)
                    self.stdscr.move(y, x-1)
            elif charlim is None or len(user_input) < charlim:  # Limit input length to 50 characters
                curses.echo()
                user_input += char
                self.stdscr.addstr(char)
                curses.noecho()
        curses.noecho()
        return user_input