import requests
import random

class LLMClient:
    def __init__(self, api_url, api_key, theme="sci-fi"):
        self.api_url = api_url
        self.api_key = api_key
        self.theme = theme
        self.cache = {}

    def generate_text(self, prompt, max_tokens=200, seed="0"):
        # if prompt in self.cache:
        #     return self.cache[prompt]

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"model": "llama-4-maverick", "max_completion_tokens": max_tokens, #seed: seed,
                "temperature": 0.1, "top_p": 1, "frequency_penalty": 0, "presence_penalty": 0,
                "messages": [
                    {"role": "user", "content": prompt}
                    ]}
        response = requests.post(self.api_url, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        text = response.json()["choices"][0]["message"]["content"].strip()
        # self.cache[prompt] = text
        return text

    def generate_name(self, type):
        prompt = f"Generate a name for a {type} in a {self.theme} setting. Try to keep it realistic. Reply with just the name."
        seed = str(random.randint(0, 1000000))
        return self.generate_text(prompt, max_tokens=10, seed=seed)