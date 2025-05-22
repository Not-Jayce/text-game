from pydantic import BaseModel, Field
from typing import Optional
import requests, threading
import time
import logging

from utils.screen import Screen
from utils.prompts import Prompts
from utils.base_utils import choice

class LLM(BaseModel):
    """
    A class representing a large language model (LLM) for generating text.
    """
    name: str = Field(...)
    token_output_cost: float = Field(...)
    token_input_cost: float = Field(...)

    @classmethod
    def create(cls, name: str, token_input_cost: float, token_output_cost: float):
        """
        Create a new LLM instance.

        :param name: The name of the LLM.
        :param token_output_cost: The cost of output tokens.
        :param token_input_cost: The cost of input tokens.
        :return: A new LLM instance.
        """
        return cls(name=name, token_input_cost=token_input_cost, token_output_cost=token_output_cost)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


LLMs = [
    LLM.create("gpt-4.1-mini", 0.28, 1.12),
    LLM.create("gpt-4o-mini", 0.105, 0.42),
    LLM.create("gpt-3.5-turbo", 0.35, 1.05),
    LLM.create("llama-4-maverick", 0.09, 0.27),
    LLM.create("claude-3-haiku-20240307", 0.225, 1.125),
    LLM.create("gemini-2.5-flash-preview", 0.06, 0.24),
    LLM.create("gemini-2.0-flash", 0.04, 0.16),
    LLM.create("gemini-1.5-flash", 0.03, 0.12),
    LLM.create("ministral-8b-latest", 0.07, 0.07),
    LLM.create("mistral-large-latest", 0.6, 1.8),
    LLM.create("dolphin-mixtral-8x22b", 0.45, 0.45),
    LLM.create("nemotron-70b", 0.0176, 0.0176),
    LLM.create("nova-lite", 0.048, 0.192),
    LLM.create("jamba-large", 0.4, 1.6),
    LLM.create("jamba-mini", 0.04, 0.08),
    LLM.create("hermes-3-405b", 0.3, 0.3),
    LLM.create("hermes-3-70b", 0.09, 0.09),
    LLM.create("phi-4", 0.014, 0.028),
    LLM.create("qwen-plus", 0.2, 0.6),
    LLM.create("minimax-01", 0.16, 0.88),
    LLM.create("deepseek-chat", 0.028, 0.056)]


class LLMClient(BaseModel):
    """
    A client for interacting with a large language model (LLM) API.
    """
    api_url: str = Field(...)
    api_key: str = Field(...)
    theme: Optional[str] = Field(None)
    screen: Optional[Screen] = Field(None, exclude=True)
    prompts: Prompts = Field(...)
    model_list: list[LLM] = Field(LLMs)
    total_cost: float = Field(0.0)

    @classmethod
    def create(cls, api_url: str, api_key: str, screen: Optional[Screen] = None, theme: Optional[str] = None):
        prompts = Prompts()
        return cls(screen=screen, prompts=prompts, api_url=api_url, api_key=api_key, theme=theme, model_list=LLMs, total_cost=0.0)
    
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
            "model": "No model specified",
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
            model: LLM = choice(self.model_list)
            data["model"] = model.name

            response = requests.post(self.api_url, headers=headers, json=data)
            if response.status_code == 200:
                try:
                    text = response.json()["choices"][0]["message"]["content"].strip()
                    input_tokens = response.json()["usage"]["prompt_tokens"]
                    output_tokens = response.json()["usage"]["completion_tokens"]
                    cost = ((input_tokens * model.token_input_cost) + (output_tokens * model.token_output_cost))/1000000
                    self.total_cost += cost
                    logging.info(f"Prompt sent to LLM with model {model} ({input_tokens} tokens): {prompt}")
                    logging.info(f"LLM response with model {model} ({output_tokens} tokens): {text}")
                    logging.info(f"LLM API cost with model {model} (total: {self.total_cost:.6} USD): {cost:.6} USD")
                    if text:
                        return text
                    else:
                        continue
                except requests.exceptions.JSONDecodeError:
                    raise Exception(f"LLM Response Error with model {data['model']}: {response.status_code} - {response.text}")
            elif response.status_code == 400 and attempt < retries - 1:
                logging.warning(f"LLM API returned 400 error with model {data['model']}. Retrying... (Attempt {attempt + 1}/{retries})")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            elif not response.json():
                logging.warning(f"LLM API returned empty result with model {data['model']}. Retrying... (Attempt {attempt + 1}/{retries})")
                # time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                logging.error(f"LLM API returned error with model {data['model']}: {response.status_code} - {response.text}")
                raise Exception(f"LLM Response Error with model {data['model']}: {response.status_code} - {response.text}")
        logging.error(f"LLM API failed after {retries} attempts with model {data['model']}.")
        raise Exception(f"LLM API failed after {retries} attempts with model {data['model']}.")
            
    def set_theme(self, theme: str):
        """
        Update the theme for the LLM client.
        """
        self.theme = theme

    def generate_int(self, gen_type:str, subject_type: str = "", load_desc: str = "", max_tokens: int = 200, return_prompt: bool = False, **kwargs: Optional[str|list[str]]) -> str|tuple[str, str]:
        kwargs["theme"] = self.theme
        kwargs["type"] = subject_type
        prompt = self.prompts.get_prompt(gen_type, **kwargs)

        gen_text = self._generate_text(prompt, max_tokens=max_tokens, loading_text=load_desc if load_desc else "Generating")
        if return_prompt:
            return gen_text, prompt
        else:
            return gen_text
        
    def generate(self, gen_type:str, subject_type: str = "", load_desc: str = "", max_tokens: int = 200, **kwargs: Optional[str|list[str]]) -> str:
        """
        Generate content with the LLM based on the type and subject.

        :param gen_type: The type of generation (e.g., "name", "description", "event").
        :param subject_type: The type of subject (e.g., "character", "region").
        :param load_desc: The loading description to display while generating.
        :param max_tokens: The maximum number of tokens to generate.
        :param kwargs: Additional keyword arguments for the prompt.
        :return: The generated text or a tuple of the generated text and the prompt.
        """
        return self.generate_int(gen_type, subject_type, load_desc, max_tokens, return_prompt=False, **kwargs) # type: ignore
    
    def generate_with_prompt(self, gen_type: str, subject_type: str = "", load_desc: str = "", max_tokens: int = 200, **kwargs: Optional[str|list[str]]) -> tuple[str, str]:
        """
        Generate content with the LLM based on the type and subject, returning the prompt used.

        :param gen_type: The type of generation (e.g., "name", "description", "event").
        :param subject_type: The type of subject (e.g., "character", "region").
        :param load_desc: The loading description to display while generating.
        :param max_tokens: The maximum number of tokens to generate.
        :param kwargs: Additional keyword arguments for the prompt.
        :return: The generated text or a tuple of the generated text and the prompt.
        """
        return self.generate_int(gen_type, subject_type, load_desc, max_tokens, return_prompt=True, **kwargs) # type: ignore
        
    def multi_generate(self, gen_count: int, gen_type: str, subject_type: str = "", load_desc: str = "", max_tokens: int = 200, **kwargs: Optional[str|list[str]]) -> list[str]:
        """
        Use multi-threading to generate multiple pieces of content with  the LLM using the same attributes.
        """
        results = []

        def generate_text(i):
            new_kwargs: dict[str,Optional[str|list[str]]] = {key: value[i] if isinstance(value, list) and len(value) == gen_count else value for key, value in kwargs.items()}
            text = self.generate(gen_type, subject_type, load_desc, max_tokens, **new_kwargs)
            if text:
                results.append(text)
            else:
                generate_text(i)

        # Split the total gen_count into groups with a maximum of 16 each.
        group_counts = []
        remaining = gen_count
        while remaining > 0:
            group_size = min(16, remaining)
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