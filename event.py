import random

class Event:
    def __init__(self, llm_client, region, characters):
        self.type = random.choice(["combat", "exploration", "interaction"])
        self.description = llm_client.generate_text(f"In the region of {region.name}, {', '.join([character.name for character in characters])} encounter a {self.type} event")
        self.outcome = None

    def resolve(self, llm_client, characters):
        prompt = f"The outcome of the {self.type} event is: "
        self.outcome = llm_client.generate_text(prompt)
        return self.outcome