from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING
import pickle, random, logging, os, time

if TYPE_CHECKING:
    from utils.screen import Screen

from support.region import Region
from support.location import Location
from support.character import Character
from utils.llm_client import LLMClient

class GameState(BaseModel):
    llm_client: LLMClient = Field(...)
    theme: str = Field(...)
    currency: int = Field(10)
    currency_name: str = Field("currency")
    recruitment_cost: int = Field(10)
    characters: List[Character] = Field(default_factory=list)
    regions: List[Region] = Field(default_factory=list)
    home_base: Region = Field(...)
    current_region: Region = Field(...)

    @classmethod
    def create(cls, llm_client: LLMClient, theme: str):
        """
        Creates a new game state with the given LLM client and theme.
        Generates characters, regions, and locations using the LLM client.

        :param llm_client: The LLM client to use for generating game content.
        :param theme: The theme for the game.
        :return: A new GameState instance.
        """
        llm_client.set_theme(theme)
        currency_name = llm_client.custom_generate(f"Create a unique name for a currency in a {theme} setting.\
                                                   Reply with just the name and no additional formatting.",
                                                   max_tokens=5, load_desc="Generating currency name")
        
        character_names = llm_client.multi_generate(3, "name", "character", "Generating character names", max_tokens=20)
        character_specializations = llm_client.multi_generate(3, "specialization", "character", "Generating character specializations")
        character_descriptions = llm_client.multi_generate(3, "specialized_description", "character", "Generating character descriptions",
                                                           name=character_names, specialization=character_specializations, max_tokens=100)
        
        region_names = llm_client.multi_generate(5, "name", "region", "Generating region names", max_tokens=20)
        region_descriptions = llm_client.multi_generate(5, "description", "region", "Generating region descriptions",
                                                       name=region_names, max_tokens=100)

        characters = [Character.create(llm_client, character_names[i], character_specializations[i], character_descriptions[i]) for i in range(3)]
        regions = [Region.create(llm_client, region_names[i], region_descriptions[i]) for i in range(5)]

        num_locations = [random.randint(2, 5) for _ in range(len(regions))]
        total_locations = sum(num_locations)

        location_names = llm_client.multi_generate(total_locations, "name", "location", "Generating location names", max_tokens=20)
        location_descriptions = llm_client.multi_generate(total_locations, "description", "location", "Generating location descriptions",
                                                           name=location_names, max_tokens=100)
        
        home_base: str = llm_client.generate("name", "home base", "Generating home base name", max_tokens=10)
        home_base_description: str = llm_client.generate("description", "home base", "Generating home base description", name=home_base, max_tokens=100)
        home_base_region = Region.create(llm_client, home_base, home_base_description)

        # Split the location names and descriptions into batches for each region
        location_index = 0
        location_names_batches = []
        location_descriptions_batches = []
        for num in num_locations:
            location_names_batches.append(location_names[location_index:location_index + num])
            location_descriptions_batches.append(location_descriptions[location_index:location_index + num])
            location_index += num

        for i, region in enumerate(regions):
            region.create_locations(llm_client, [Location.create(llm_client, region.name, i+1, location_names_batches[i][j],
                                                 location_descriptions_batches[i][j]) for j in range(num_locations[i])])

        return cls(
            llm_client=llm_client,
            characters=characters,
            regions=regions,
            current_region=home_base_region,
            theme=theme,
            currency_name=currency_name,
            currency=10,
            recruitment_cost=10,
            home_base=home_base_region
        )

    @classmethod
    def load(cls, screen: "Screen", data: bytes):
        try:
            game_state: GameState = pickle.loads(data)

            if not game_state.llm_client:
                api_key = os.getenv("API_KEY")
                api_url = os.getenv("API_URL")
                if not api_key or not api_url:
                    screen.temp_display(2, "Error: API key or URL not found in environment variables.")
                    logging.error("Error: API key or URL not found in environment variables.")
                    time.sleep(2)
                    return None
                game_state.llm_client = LLMClient.create(api_url, api_key, screen, game_state.theme)

            game_state.llm_client.screen = screen
            logging.info("Game state loaded successfully.")
        except EOFError:
            logging.error("Error loading game state: File is empty or corrupted.")
        except Exception as e:
            logging.error(f"Error loading game state: {e}")
        return game_state
    
    def save(self, filename: Optional[str] = 'save.dat'):
        if not filename:
            filename = 'save.dat'
        filename = filename if filename.endswith('.dat') else filename + '.dat'
        try:
            with open(filename, 'wb') as f:
                f.write(pickle.dumps(self))
            logging.info("Game state saved successfully.")
        except Exception as e:
            logging.error(f"Error saving game state: {e}")

    def set_theme(self, theme: str):
        self.theme = theme
        if self.llm_client:
            self.llm_client.set_theme(theme)
        else:
            logging.error("LLM client is not set. Cannot set theme.")