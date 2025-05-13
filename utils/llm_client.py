from pydantic import BaseModel, Field
from typing import Optional
import requests
import random

class LLMClient(BaseModel):
    """
    A client for interacting with a large language model (LLM) API.
    """
    api_url: str = Field(...)
    api_key: str = Field(...)
    theme: Optional[str] = Field(None)

    def generate_text(self, prompt: str, max_tokens: int = 200) -> str:
        print(prompt)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {
            "model": "llama-4-maverick",
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        retries = 3
        for attempt in range(retries):
            response = requests.post(self.api_url, headers=headers, json=data)
            if response.status_code == 200:
                try:
                    text = response.json()["choices"][0]["message"]["content"].strip()
                    return text
                except requests.exceptions.JSONDecodeError:
                    raise Exception(f"LLM Response Error: {response.status_code} - {response.text}")
            elif response.status_code == 400 and attempt < retries - 1:
                continue
            else:
                raise Exception(f"LLM Response Error: {response.status_code} - {response.text}")
            
    def set_theme(self, theme: str):
        """
        Update the theme for the LLM client.
        """
        self.theme = theme

    def generate_name(self, type: str) -> str:
        seed = str(random.randint(0, 1000000))
        prompt = f"Seed: {seed}. Generate a unique name for a {type} in a {self.theme} setting. Try to keep it realistic. Reply with just the name."
        return self.generate_text(prompt, max_tokens=7)

    def generate_description(self, type: str, name: str) -> str:
        seed = str(random.randint(0, 1000000))
        prompt = f"Seed: {seed}. Generate a one-sentence description for a {type} named {name} in a {self.theme} setting. Try to keep it realistic. Reply with just the description."
        return self.generate_text(prompt, max_tokens=30)
    
    def generate_outcome(self, prompt: str, description: str, outcome: str) -> str:
        seed = str(random.randint(0, 1000000))
        prompt = f"Seed: {seed}. Generate a 1-paragraph outcome for the event described below with the outcome '{outcome}' in a {self.theme} setting.\
              Reply with just the outcome.\nEvent prompt: {prompt}\nEvent description: {description}"
        return self.generate_text(prompt, max_tokens=200)
    
    @classmethod
    def create(cls, api_url: str, api_key: str, theme: str = None):
        return cls(api_url=api_url, api_key=api_key, theme=theme)