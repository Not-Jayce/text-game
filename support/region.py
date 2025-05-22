import random
from pydantic import BaseModel, Field
from typing import List, Optional

from support.location import Location
from utils.llm_client import LLMClient
from support.event import Event, event_screen

class Region(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    hazard_level: int = Field(...)
    locations: List[Location] = Field(default_factory=list)

    def create_locations(self, llm_client: LLMClient, locations: Optional[List[Location]] = None):
        """
        Creates locations for the region using the LLM client.
        If locations are provided, they will be used instead of generating new ones.

        :param llm_client: The LLM client to use for generating locations.
        :param locations: Optional list of locations to use instead of generating new ones.
        """
        if locations is None:
            num_locations = random.randint(2, 5)

            location_names = llm_client.multi_generate(num_locations, "name", f"location in {self.name} region",
                                                    "Generating location names", max_tokens=20)
            location_descriptions = llm_client.multi_generate(num_locations, "description", f"location in {self.name} region",
                                                            "Generating location descriptions",
                                                            name=location_names, max_tokens=100)
            try:
                self.locations = [Location.create(llm_client, self.name, i+1, location_names[i],
                                            location_descriptions[i]) for i in range(num_locations)]
            except IndexError:
                print("Error: Not enough location names or descriptions generated.")
                print(f"Generated names: {location_names}")
                print(f"Generated descriptions: {location_descriptions}")
        
        else:
            self.locations = locations

    @classmethod
    def create(cls, llm_client: LLMClient, name: Optional[str] = None, description: Optional[str] = None):
        """
        Creates a new region using the LLM client.
        If name and description are provided, they will be used instead of generating new ones.

        :param llm_client: The LLM client to use for generating the region.
        :param name: Optional name for the region.
        :param description: Optional description for the region.
        :return: A new Region instance.
        """
        if name is None:
            name = llm_client.generate("name", "region", "Generating regions", max_tokens=20)
        if description is None:
            description = llm_client.generate("description", "region", "Generating regions", name=name, max_tokens=100)
        return cls(
            name=name,
            description=description,
            hazard_level=random.randint(0, 4),
            locations=[],
        )

    def region_screen(self, screen, game_state):
        """
        Displays the region screen, listing visible locations and allowing the user to select a location to visit.
        :param screen: The Screen instance for display.
        :param game_state: The current GameState instance.
        """
        while True:
            visible_locations = [loc for loc in self.locations if loc.discovered]
            if not visible_locations:
                screen.display(f"No locations discovered yet in {self.name}.", f"Hazard Level: {self.hazard_level}")
                screen.add_new_line("Press 'b' to go back.")
                c = screen.handle_keypress(game_state)
                if c == ord('b'):
                    break
                continue

            options = [f"{loc.name} (Distance: {loc.distance})" for loc in visible_locations]
            screen.display_options(f"{self.name} (Hazard Level: {self.hazard_level})\nSelect a location to visit:", options)
            screen.add_new_line(f"Enter 1-{len(visible_locations)} to visit, or 'b' to go back.")
            c = screen.handle_keypress(game_state)
            if c >= ord('1') and c < ord('1') + len(visible_locations):
                location_index = c - ord('1')
                selected_location = visible_locations[location_index]
                # Show location description and ask for confirmation
                while True:
                    screen.display(f"{selected_location.name}", f"{selected_location.description}", f"Distance: {selected_location.distance}")
                    screen.add_new_line("Press 'y' to confirm, or 'b' to return to location selection.")
                    confirm = screen.handle_keypress(game_state)
                    if confirm == ord('y'):
                        screen.temp_display(2, f"Traveling to {selected_location.name}...")
                        characters = getattr(game_state, 'characters', [])
                        event = Event.create(game_state, self, characters)
                        event_screen(screen, event, game_state)
                        break
                    elif confirm == ord('b'):
                        break
            elif c == ord('b'):
                break

