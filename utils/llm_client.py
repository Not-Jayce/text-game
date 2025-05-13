from pydantic import BaseModel, Field
from typing import Optional
import requests, threading
import random, time

from utils.screen import Screen
from utils.prompts import Prompts

class LLMClient(BaseModel):
    """
    A client for interacting with a large language model (LLM) API.
    """
    api_url: str = Field(...)
    api_key: str = Field(...)
    theme: Optional[str] = Field(None)
    screen: Screen = Field(...)
    prompts: Prompts = Field(...)

    @classmethod
    def create(cls, screen: Screen, api_url: str, api_key: str, theme: str = None):
        prompts = Prompts()
        return cls(screen=screen, prompts=prompts, api_url=api_url, api_key=api_key, theme=theme)

    def _generate_text(self, prompt: str, max_tokens: int,  loading_text: str) -> str:
        # Create a thread to generate the text
        text = []
        def generate_text_thread():
            text.append(self._run_generation(prompt, max_tokens))
        thread = threading.Thread(target=generate_text_thread)
        thread.start()

        # Display a spinning wheel loading animation while the text is being generated
        loading_chars = ['/', '-', '\\', '|']
        i = 0
        start_time = time.time()
        while thread.is_alive():
            if time.time() - start_time > 1:
                self.screen.display(f"{loading_text}... " + loading_chars[i])
                i = (i + 1) % len(loading_chars)
                time.sleep(0.2)

        # Return the generated text
        return text[0]

    def _run_generation(self, prompt: str, max_tokens: int) -> str:
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

        retries = 5
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

    def generate(self, gen_type:str, subject_type: str = "", load_desc: str = "", max_tokens: int = 200, return_prompt: bool = False, **kwargs) -> str|tuple[str, str]:
        """
        Generate content with the LLM based on the type and subject.

        :param gen_type: The type of generation (e.g., "name", "description", "event").
        :param subject_type: The type of subject (e.g., "character", "region").
        :param load_desc: The loading description to display while generating.
        :param max_tokens: The maximum number of tokens to generate.
        :param return_prompt: Whether to return the generated text and the prompt.
        :param kwargs: Additional keyword arguments for the prompt.
        :return: The generated text or a tuple of the generated text and the prompt.
        """
        kwargs["theme"] = self.theme
        kwargs["type"] = subject_type
        prompt = self.prompts.get_prompt(gen_type, **kwargs)

        gen_text = self._generate_text(prompt, max_tokens=max_tokens, loading_text=load_desc if load_desc else "Generating...")
        if return_prompt:
            return gen_text, prompt
        else:
            return gen_text
        
    def multi_generate(self, gen_count: int, gen_type: str, subject_type: str = "", load_desc: str = "", max_tokens: int = 200, **kwargs) -> list[str]:
        """
        Use multi-threading to generate multiple pieces of content with  the LLM using the same attributes.
        """
        threads = []
        results = []

        def generate_text(i):
            new_kwargs = {key: value[i] if isinstance(value, list) and len(value) == gen_count else value for key, value in kwargs.items()}
            text = self.generate(gen_type, subject_type, load_desc, max_tokens, **new_kwargs)
            if text:
                results.append(text)
            else:
                generate_text(i)

        for i in range(gen_count):
            thread = threading.Thread(target=generate_text, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        return results
    
    def custom_generate(self, prompt: str, max_tokens: int = 200, load_desc: str = "") -> str:
        """
        Generate custom content with the LLM based on the provided prompt.
        """
        return self._generate_text(prompt, max_tokens=max_tokens, loading_text=load_desc if load_desc else "Generating...")