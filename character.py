import random

class Character:
    def __init__(self, llm_client):
        self.name = llm_client.generate_name("character")
        self.specialization = random.choice(["engineer", "scientist", "soldier"])
        self.talent = random.choice(["polymath", "capable", "planner"])
        self.level = 1
        self.xp = 0
        self.hp = self.level
        self.gear = []

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.level * 100:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.hp = self.level
        self.xp = 0

    def to_dict(self):
        return {
        'name': self.name,
        'specialization': self.specialization,
        'talent': self.talent,
        'level': self.level,
        'xp': self.xp,
        'hp': self.hp,
        'gear': self.gear
        }

    @classmethod
    def from_dict(cls, llm_client, data):
        character = cls(llm_client)
        character.name = data['name']
        character.specialization = data['specialization']
        character.talent = data['talent']
        character.level = data['level']
        character.xp = data['xp']
        character.hp = data['hp']
        character.gear = data['gear']
        return character