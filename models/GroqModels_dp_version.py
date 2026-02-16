import os
from groq import Groq
from models.LLMBase import LLMBase

class GroqModels(LLMBase):
    def __init__(self, api_key=None, model="llama-3.1-8b-instant", max_tokens=256, temperature=0.7, system_prompt = None):
        self.model_name_hf = model
        self.tokenizer = None

        # for Defensive prompting
        if system_prompt is not None:
            self.system_prompt = system_prompt
        ###############################

        super().__init__(api_key=api_key)

        if api_key:
            self.client = Groq(api_key=api_key)
        elif "GROQ_API_KEY" in os.environ:
            self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
        else:
            self.client = Groq()

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def load_model(self):
        pass

    def query(self, prompt):
        return self.query_remote_model(prompt)

    def query_remote_model(self, prompt_or_messages):
        try:
            messages = []

            if hasattr(self, "system_prompt") and self.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.system_prompt
                })

            if isinstance(prompt_or_messages, list):
                messages.extend(prompt_or_messages)
            else:
                messages.append({
                "role": "user",
                "content": str(prompt_or_messages)
            })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API Error: {e}")
            return ""
