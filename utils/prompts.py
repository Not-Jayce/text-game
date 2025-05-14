import random
from pydantic import BaseModel
from typing import Dict

class Prompts(BaseModel):
    """
    This class contains the prompts used for the LLM.
    """
    prompts: Dict[str, str] = {
        "name": "Generate a unique name for a {type} in a {theme} setting. Try to keep it realistic.\
            Reply with just the name in plaintext with no formatting.",

        "specialized_description": "Generate a one-sentence description for a {type} named {name} in a {theme}\
            setting. The {type} is a {specialization}. Try to keep it realistic. Reply with just the description and no additional formatting.",

        "specialization": "Generate a unique specialization (trade or skill) for a {type} in a {theme} setting in 1 or 2 words. Try to keep it realistic.\
            Reply with just the specialization and no additional formatting.",

        "description": "Generate a one-sentence description for a {type} named {name} in a {theme}\
            setting. Try to keep it realistic. Reply with just the description and no additional formatting.",

        "event": "In the {theme} themed region of {region}, {characters}\
            encounter a(n) {type} event. In 1 paragraph, describe the beginning of this encounter, before any actions are taken.",

        "outcome": "Generate a 1-paragraph outcome for the event described below with the outcome '{outcome}' in a \
            {theme} setting. Reply with just the outcome.\nEvent prompt: {prompt}\nEvent description: {description}",
    }

    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get a prompt by its name and substitute in the relevant values.
        """
        seed = str(random.randint(0, 1000000))
        if prompt_name in self.prompts:
            prompt = f"Seed: {seed}. " + self.prompts[prompt_name]
            try:
                prompt = prompt.format(**kwargs)
            except KeyError as e:
                raise ValueError(f"Missing value in prompt {prompt_name}: {e}")
        else:
            raise ValueError(f"Prompt '{prompt_name}' not found.")
        return prompt