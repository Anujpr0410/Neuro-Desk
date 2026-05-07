"""
Unified LLM Client for NeuroDesk AI Multi-Agent System.
Supports multiple providers: Ollama, OpenRouter, NVIDIA NIM, Google Gemini, OpenAI.
"""

import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncIterator
from dataclasses import dataclass
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class LLMResponse:
    """Unified response object for all LLM providers."""
    text: str
    raw: Any = None
    model: str = ""
    provider: str = ""


class LLMClient:
    """Unified LLM client supporting multiple providers."""

    def __init__(self, provider: str, api_key: str = "", model: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self._clients = {}

    def _get_ollama_client(self):
        """Initialize Ollama client."""
        if "ollama" not in self._clients:
            try:
                import ollama
                self._clients["ollama"] = ollama
            except ImportError:
                raise ImportError("Ollama package not installed. Run: pip install ollama")
        return self._clients["ollama"]

    def _get_openai_client(self):
        """Initialize OpenAI-compatible client."""
        if "openai" not in self._clients:
            try:
                import openai
                self._clients["openai"] = openai
            except ImportError:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
        return self._clients["openai"]

    def _get_google_client(self):
        """Initialize Google Gemini client."""
        if "google" not in self._clients:
            try:
                import google.generativeai as genai
                self._clients["google"] = genai
            except ImportError:
                raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
        return self._clients["google"]

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Any:
        """Chat with the LLM using configured provider."""
        try:
            if self.provider == "Ollama":
                gen = self._chat_ollama(messages, system_prompt, stream, temperature, max_tokens)
            elif self.provider == "OpenRouter":
                gen = self._chat_openrouter(messages, system_prompt, stream, temperature, max_tokens)
            elif self.provider == "NVIDIA NIM":
                gen = self._chat_nvidia(messages, system_prompt, stream, temperature, max_tokens)
            elif self.provider == "Google Gemini":
                gen = self._chat_gemini(messages, system_prompt, stream, temperature, max_tokens)
            elif self.provider == "OpenAI":
                gen = self._chat_openai(messages, system_prompt, stream, temperature, max_tokens)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
                
            if stream:
                async def _stream_wrapper():
                    async for chunk in gen:
                        yield chunk
                return _stream_wrapper()
            else:
                # Consume the generator to get the final LLMResponse
                final_response = None
                async for chunk in gen:
                    final_response = chunk
                return final_response
        except Exception as e:
            raise Exception(f"LLM {self.provider} error: {str(e)}")

    async def _chat_ollama(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Chat with Ollama local LLM."""
        import ollama

        # Build messages with system prompt
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = ollama.chat(
            model=self.model,
            messages=full_messages,
            stream=stream,
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )

        if stream:
            # Handle streaming for Ollama - only yield text chunks
            for chunk in response:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
        else:
            yield LLMResponse(
                text=response["message"]["content"],
                raw=response,
                model=self.model,
                provider="Ollama"
            )

    async def _chat_openrouter(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Chat with OpenRouter API."""
        import openai

        client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            yield LLMResponse(
                text=response.choices[0].message.content,
                raw=response,
                model=self.model,
                provider="OpenRouter"
            )

    async def _chat_nvidia(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Chat with NVIDIA NIM API."""
        import openai

        client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            yield LLMResponse(
                text=response.choices[0].message.content,
                raw=response,
                model=self.model,
                provider="NVIDIA NIM"
            )

    async def _chat_gemini(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Chat with Google Gemini API."""
        genai = self._get_google_client()
        genai.configure(api_key=self.api_key)

        # Convert messages format for Gemini
        history = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            history.append({
                "role": role,
                "parts": [msg["content"]]
            })

        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_prompt if system_prompt else None
        )

        chat = model.start_chat(history=history if history else None)

        response = chat.send_message(
            messages[-1]["content"] if messages else "",
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            },
            stream=stream
        )

        if stream:
            for chunk in response:
                yield chunk.text
        else:
            yield LLMResponse(
                text=response.text,
                raw=response,
                model=self.model,
                provider="Google Gemini"
            )

    async def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Chat with OpenAI API."""
        client = self._get_openai_client()

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            yield LLMResponse(
                text=response.choices[0].message.content,
                raw=response,
                model=self.model,
                provider="OpenAI"
            )


async def stream_response(response_gen, callback):
    """Helper to stream response tokens to callback."""
    full_text = ""
    async for chunk in response_gen:
        full_text += chunk
        await callback(chunk)
    return full_text


# Provider models mapping for UI suggestions
PROVIDER_MODELS = {
    "Ollama": {
        "description": "Local LLM - No API key required",
        "suggested_models": [
            "llama3:8b", "llama3:70b", "mistral:7b", "codellama:7b",
            "gemma:7b", "phi3:3b", "qwen:7b"
        ]
    },
    "OpenRouter": {
        "description": "Free models available - API key required",
        "suggested_models": [
            "meta-llama/llama-3-8b-instruct:free",
            "meta-llama/llama-3-70b-instruct:free",
            "google/gemma-7b-it:free",
            "microsoft/phi-3-mini-128k-instruct:free"
        ]
    },
    "NVIDIA NIM": {
        "description": "Free credits available - API key required",
        "suggested_models": [
            "meta/llama3-8b-instruct", "meta/llama3-70b-instruct",
            "mistralai/mistral-7b-instruct", "google/gemma-7b"
        ]
    },
    "Google Gemini": {
        "description": "Google's AI model - API key required",
        "suggested_models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
    },
    "OpenAI": {
        "description": "OpenAI models - API key required",
        "suggested_models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o-mini"]
    }
}


def get_provider_models(provider: str) -> List[str]:
    """Get suggested models for a provider."""
    if provider in PROVIDER_MODELS:
        return PROVIDER_MODELS[provider]["suggested_models"]
    return []


async def fetch_available_models(provider: str, api_key: str = "") -> List[str]:
    """Fetch available models from the specified provider dynamically."""
    try:
        if provider == "Ollama":
            import ollama
            response = ollama.list()
            models_out = []
            # response.models is a list of Model objects; .model attribute holds the name string
            if hasattr(response, 'models') and response.models:
                for m in response.models:
                    name = getattr(m, 'model', None) or getattr(m, 'name', None) or str(m)
                    if name:
                        models_out.append(name)
            elif isinstance(response, dict) and 'models' in response:
                for m in response['models']:
                    name = m.get('model') or m.get('name') or m.get('id', '')
                    if name:
                        models_out.append(name)
            return models_out

        
        elif provider in ["OpenRouter", "NVIDIA NIM", "OpenAI"]:
            import openai
            
            base_url = None
            if provider == "OpenRouter":
                base_url = "https://openrouter.ai/api/v1"
            elif provider == "NVIDIA NIM":
                base_url = "https://integrate.api.nvidia.com/v1"
                
            client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            # Using sync call in an async wrapper is fine here since it's just a config setup call
            models = client.models.list()
            return [m.id for m in models.data]
            
        elif provider == "Google Gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            models = genai.list_models()
            return [m.name.replace('models/', '') for m in models]
            
        else:
            raise ValueError(f"Unknown provider: {provider}")
            
    except Exception as e:
        raise Exception(f"Failed to fetch models for {provider}: {str(e)}")
