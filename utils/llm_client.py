from pydantic import BaseModel, Field
from typing import Optional, Callable
import requests, threading
import random, time
import logging

from utils.screen import Screen
from utils.prompts import Prompts

class LLMClient(BaseModel):
    """
    A client for interacting with a large language model (LLM) API.
    """
    api_url: str = Field(...)
    api_key: str = Field(...)
    theme: Optional[str] = Field(None)
    screen: Optional[Screen] = Field(None)
    prompts: Prompts = Field(...)

    @classmethod
    def create(cls, api_url: str, api_key: str, screen: Optional[Screen] = None, theme: Optional[str] = None):
        prompts = Prompts()
        return cls(screen=screen, prompts=prompts, api_url=api_url, api_key=api_key, theme=theme)
    
    def set_screen(self, screen: Screen):
        """
        Set the screen for the LLM client.
        """
        self.screen = screen

    def _generate_text(self, prompt: str, max_tokens: int,  loading_text: str) -> str:
        """
        Generate text using the LLM API with a loading animation. Internal function.
        """
        # Create a thread to generate the text
        text = []
        def generate_text_thread():
            text.append(self._run_generation(prompt, max_tokens))
        thread = threading.Thread(target=generate_text_thread)
        thread.start()

        # Display a spinning wheel loading animation while the text is being generated
        if self.screen:
            loading_chars = ['/', '-', '\\', '|']
            i = 0
            start_time = time.time()
            while thread.is_alive():
                if time.time() - start_time > 0:
                    self.screen.display(f"{loading_text}... " + loading_chars[i])
                    i = (i + 1) % len(loading_chars)
                    time.sleep(0.2)

        # Return the generated text
        return text[0] if text else ""

    def _run_generation(self, prompt: str, max_tokens: int) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {
            "model": "llama-4-maverick",
            "max_tokens": max_tokens,
            "temperature": 0.5,
            "top_p": 0.8,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "messages": [
                {"role": "system", "content": f"You produce unique but relevant outputs each time you receive a prompt.\
                 Use the seed to generate a unique response, but don't include the seed in your response. Always reply with plaintext and no formatting or headings."},
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
                logging.warning(f"LLM API returned 400 error. Retrying... (Attempt {attempt + 1}/{retries})")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            elif not response.json():
                logging.warning(f"LLM API returned emptry result. Retrying... (Attempt {attempt + 1}/{retries})")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                logging.error(f"LLM API returned error: {response.status_code} - {response.text}")
                raise Exception(f"LLM Response Error: {response.status_code} - {response.text}")
        logging.error(f"LLM API failed after {retries} attempts.")
        raise Exception(f"LLM API failed after {retries} attempts.")
            
    def set_theme(self, theme: str):
        """
        Update the theme for the LLM client.
        """
        self.theme = theme

    def generate(self, gen_type:str, subject_type: str = "", load_desc: str = "", max_tokens: int = 200, return_prompt: bool = False, **kwargs: Optional[str|list[str]]) -> str|tuple[str, str]:
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

        gen_text = self._generate_text(prompt, max_tokens=max_tokens, loading_text=load_desc if load_desc else "Generating")
        logging.info(f"Prompt sent to LLM: {prompt}")
        logging.info(f"Generated text: {gen_text}")
        if return_prompt:
            return gen_text, prompt
        else:
            return gen_text
        
    def multi_generate(self, gen_count: int, gen_type: str, subject_type: str = "", load_desc: str = "", max_tokens: int = 200, **kwargs: Optional[str|list[str]]) -> list[str]:
        """
        Use multi-threading to generate multiple pieces of content with  the LLM using the same attributes.
        """
        results = []

        def generate_text(i):
            new_kwargs: dict[str,Optional[str|list[str]]] = {key: value[i] if isinstance(value, list) and len(value) == gen_count else value for key, value in kwargs.items()}
            text = self.generate(gen_type, subject_type, load_desc, max_tokens, return_prompt=False, **new_kwargs)
            if text:
                results.append(text)
            else:
                generate_text(i)

        # Split the total gen_count into groups with a maximum of 8 each.
        group_counts = []
        remaining = gen_count
        while remaining > 0:
            group_size = min(8, remaining)
            group_counts.append(group_size)
            remaining -= group_size

        def kwargs_dict(idx: int) -> dict[str, Optional[str|list[str]]]:
            """
            Create a dictionary of keyword arguments for the generate function.
            """
            return {key: value[idx] if isinstance(value, list) and len(value) == gen_count else value for key, value in kwargs.items()}

        # Generate the text in groups of up to 8 to prevent overwhelming the API.
        for gen_group in group_counts:
            batch_results = [None] * gen_group
            batch_threads = []
            for i in range(gen_group):
                thread = threading.Thread(
                    target=lambda idx=i: batch_results.__setitem__(
                        idx,
                        self.generate(
                            gen_type,
                            subject_type,
                            load_desc,
                            max_tokens,
                            return_prompt=False,
                            **kwargs_dict(idx)
                        )
                    )
                )
                batch_threads.append(thread)
                thread.start()

            for thread in batch_threads:
                thread.join()

            results.extend(batch_results)

        return results
    
    def custom_generate(self, prompt: str, max_tokens: int = 200, load_desc: str = "") -> str:
        """
        Generate custom content with the LLM based on the provided prompt.
        """
        return self._generate_text(prompt, max_tokens=max_tokens, loading_text=load_desc if load_desc else "Generating...")