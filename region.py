import random

class Region:
    def __init__(self, llm_client):
        self.name = llm_client.generate_name("region")
        self.description = llm_client.generate_text(f"Describe the region of {self.name}")
        self.hazard_level = random.randint(0, 4)
        self.locations = []

    def add_location(self, location):
        self.locations.append(location)

    def to_dict(self):
        return {
        'name': self.name,
        'description': self.description,
        'hazard_level': self.hazard_level,
        'locations': self.locations
        }

    @classmethod
    def from_dict(cls, llm_client, data):
        region = cls(llm_client)
        region.name = data['name']
        region.description = data['description']
        region.hazard_level = data['hazard_level']
        region.locations = data['locations']
        return region