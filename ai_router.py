"""
==============================================================================
AI Router - High-Availability Multi-Provider FREE AI Setup
==============================================================================
Priority Fallback Architecture:
  [1] Groq        (PRIMARY)    -> Ultra-fast Llama 3.3 / Qwen inference
  [2] Gemini      (SECONDARY)  -> High-quota Google AI Studio Flash tier
  [3] OpenRouter  (FALLBACK 1) -> Free community models (:free tier)
  [4] Mistral AI  (FALLBACK 2) -> Free experiment tier
  [5] HuggingFace (FALLBACK 3) -> Free Serverless Inference API

Features:
- Automatic failover on HTTP 429 (Rate Limit), timeouts, connection errors, 5xx
- Zero hardcoded keys; dynamically loads from .env using python-dotenv
- Sensitive token masking in all logs and error messages
- Supports simple text prompt or structured JSON mode
- Seamless integration with DEMETER / DEM3T3R V1 / Robot Swarm
==============================================================================
"""

import os
import time
import json
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Setup Environment & Logging
# ---------------------------------------------------------------------------
# Search for .env in current directory, parent directories, or standard locations
_env_paths = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env"
]
for p in _env_paths:
    if p.exists():
        load_dotenv(dotenv_path=p, override=False)
        break
else:
    load_dotenv(override=False)

logger = logging.getLogger("AIRouter")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)


def mask_token(token: Optional[str]) -> str:
    """Safely mask API key for logging and security."""
    if not token:
        return "<NOT_SET>"
    token = token.strip()
    if len(token) <= 8:
        return "********"
    return f"{token[:4]}...{token[-4:]}"


# ---------------------------------------------------------------------------
# Provider Definitions with Currently Available Free-Tier Models
# ---------------------------------------------------------------------------
class AIProvider:
    """Encapsulates a single AI provider configuration and request logic."""
    def __init__(
        self,
        name: str,
        env_key_name: str,
        endpoint: str,
        models: List[str],
        headers_factory,
        payload_formatter,
        response_parser,
        extra_keys: Optional[List[str]] = None
    ):
        self.name = name
        self.env_key_name = env_key_name
        self.endpoint = endpoint
        self.models = models
        self.headers_factory = headers_factory
        self.payload_formatter = payload_formatter
        self.response_parser = response_parser
        self.extra_keys = extra_keys or []
        self._rate_limited_until = 0.0

    def get_api_keys(self) -> List[str]:
        """Fetch all available API keys for this provider from environment."""
        keys = []
        primary = os.getenv(self.env_key_name, "").strip()
        if primary and "your-" not in primary:
            keys.append(primary)
        for k in self.extra_keys:
            val = os.getenv(k, "").strip()
            if val and "your-" not in val and val not in keys:
                keys.append(val)
        return keys

    def is_configured(self) -> bool:
        return len(self.get_api_keys()) > 0

    def is_rate_limited(self) -> bool:
        return time.time() < self._rate_limited_until

    def mark_rate_limited(self, duration_sec: float = 60.0):
        self._rate_limited_until = time.time() + duration_sec


# ---------------------------------------------------------------------------
# Provider Implementation Specs (OpenAI-Compatible & Native Endpoints)
# ---------------------------------------------------------------------------

def _groq_payload(model, prompt, system_prompt, max_tokens, temperature, json_mode):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    return payload


def _groq_parse(res_json):
    return res_json["choices"][0]["message"]["content"]


def _gemini_headers(api_key):
    return {"Content-Type": "application/json"}


def _gemini_payload(model, prompt, system_prompt, max_tokens, temperature, json_mode):
    contents = []
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"System Instructions: {system_prompt}\n\nUser Request: {prompt}"
    contents.append({"parts": [{"text": full_prompt}]})
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature
        }
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"
    return payload


def _gemini_parse(res_json):
    candidates = res_json.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned empty candidate list")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError("Gemini returned empty parts")
    return parts[0].get("text", "")


def _openai_compatible_payload(model, prompt, system_prompt, max_tokens, temperature, json_mode):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    return payload


def _openai_compatible_parse(res_json):
    return res_json["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Build Registry of Free Tier Providers (Strict Priority Order)
# ---------------------------------------------------------------------------
def build_providers() -> List[AIProvider]:
    providers = [
        # [1] Groq - PRIMARY
        AIProvider(
            name="Groq",
            env_key_name="GROQ_API_KEY",
            endpoint="https://api.groq.com/openai/v1/chat/completions",
            models=["qwen/qwen3.8-27b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            headers_factory=lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
            payload_formatter=_groq_payload,
            response_parser=_groq_parse
        ),
        # [2] Google Gemini - SECONDARY
        AIProvider(
            name="Gemini",
            env_key_name="GEMINI_API_KEY",
            endpoint="https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
            models=["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-2.0-flash-exp", "gemini-1.5-flash-latest"],
            headers_factory=_gemini_headers,
            payload_formatter=_gemini_payload,
            response_parser=_gemini_parse,
            extra_keys=["GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]
        ),
        # [3] OpenRouter - FALLBACK 1
        AIProvider(
            name="OpenRouter",
            env_key_name="OPENROUTER_API_KEY",
            endpoint="https://openrouter.ai/api/v1/chat/completions",
            models=[
                "meta-llama/llama-3.3-70b-instruct:free",
                "deepseek/deepseek-r1:free",
                "google/gemini-2.0-flash-exp:free",
                "qwen/qwen-2.5-72b-instruct:free",
                "mistralai/mistral-7b-instruct:free"
            ],
            headers_factory=lambda k: {
                "Authorization": f"Bearer {k}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://cropguard.ai",
                "X-Title": "DEM3T3R V1"
            },
            payload_formatter=_openai_compatible_payload,
            response_parser=_openai_compatible_parse
        ),
        # [4] Mistral AI - FALLBACK 2
        AIProvider(
            name="Mistral",
            env_key_name="MISTRAL_API_KEY",
            endpoint="https://api.mistral.ai/v1/chat/completions",
            models=["mistral-small-latest", "open-mistral-7b", "open-mixtral-8x7b"],
            headers_factory=lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
            payload_formatter=_openai_compatible_payload,
            response_parser=_openai_compatible_parse
        ),
        # [5] Hugging Face - FALLBACK 3
        AIProvider(
            name="HuggingFace",
            env_key_name="HUGGINGFACE_API_KEY",
            endpoint="https://api-inference.huggingface.co/v1/chat/completions",
            models=["meta-llama/Llama-3.2-3B-Instruct", "Qwen/Qwen2.5-72B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"],
            headers_factory=lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
            payload_formatter=_openai_compatible_payload,
            response_parser=_openai_compatible_parse,
            extra_keys=["HF_TOKEN"]
        )
    ]
    return providers


# ---------------------------------------------------------------------------
# AIRouter Engine
# ---------------------------------------------------------------------------
class AIRouter:
    """Multi-Provider AI Router with Automatic Failover and Retry Protection."""

    def __init__(self, default_timeout: int = 12, max_retries: int = 2):
        self.default_timeout = int(os.getenv("AI_ROUTER_TIMEOUT", default_timeout))
        self.max_retries = int(os.getenv("AI_ROUTER_MAX_RETRIES", max_retries))
        self.providers = build_providers()

    def get_health_status(self) -> Dict[str, str]:
        """Returns the configuration & rate-limit status of all providers."""
        status = {}
        for p in self.providers:
            if not p.is_configured():
                status[p.name] = "NOT CONFIGURED"
            elif p.is_rate_limited():
                status[p.name] = "RATE LIMITED"
            else:
                keys_count = len(p.get_api_keys())
                status[p.name] = f"AVAILABLE ({keys_count} key{'s' if keys_count > 1 else ''})"
        return status

    def test_provider(self, provider_name: str, test_prompt: str = "Reply with 'OK' and nothing else.") -> Dict[str, Any]:
        """Test a single specific provider."""
        provider = next((p for p in self.providers if p.name.lower() == provider_name.lower()), None)
        if not provider:
            return {"provider": provider_name, "status": "UNKNOWN PROVIDER", "error": "Provider not in registry"}
        
        if not provider.is_configured():
            return {"provider": provider.name, "status": "NOT CONFIGURED", "error": f"Set {provider.env_key_name} in .env"}

        for key in provider.get_api_keys():
            for model in provider.models:
                try:
                    res_text = self._call_provider(provider, key, model, test_prompt, None, 50, 0.2, False, 8)
                    return {
                        "provider": provider.name,
                        "status": "AVAILABLE",
                        "model": model,
                        "sample_response": res_text.strip()
                    }
                except Exception as e:
                    last_err = str(e)
        return {"provider": provider.name, "status": "FAILED", "error": last_err}

    def _call_provider(
        self,
        provider: AIProvider,
        api_key: str,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        json_mode: bool,
        timeout: int
    ) -> str:
        """Executes a single HTTP call to the provider."""
        headers = provider.headers_factory(api_key)
        payload = provider.payload_formatter(model, prompt, system_prompt, max_tokens, temperature, json_mode)
        
        # Format endpoint URL (Gemini requires key and model in URL)
        if "{model}" in provider.endpoint or "{key}" in provider.endpoint:
            url = provider.endpoint.format(model=model, key=api_key)
        else:
            url = provider.endpoint

        response = requests.post(url, json=payload, headers=headers, timeout=timeout)

        # Handle Rate Limits (HTTP 429)
        if response.status_code == 429:
            provider.mark_rate_limited(60.0)
            raise RuntimeError(f"HTTP 429 Rate Limit Exceeded for {provider.name}")

        # Handle Auth Errors
        if response.status_code in (401, 403):
            raise PermissionError(f"HTTP {response.status_code} Authentication Failed for {provider.name}")

        # Handle Model Not Found (HTTP 404)
        if response.status_code == 404:
            raise LookupError(f"HTTP 404 Model '{model}' not found on {provider.name}")

        # Handle Server Errors (HTTP 5xx)
        if response.status_code >= 500:
            raise RuntimeError(f"HTTP {response.status_code} Server Error on {provider.name}")

        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code} Error: {response.text[:200]}")

        res_json = response.json()
        parsed_text = provider.response_parser(res_json)
        return parsed_text

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        json_mode: bool = False,
        timeout: Optional[int] = None
    ) -> str:
        """
        Routes prompt through providers in priority order with auto failover.
        """
        call_timeout = timeout or self.default_timeout
        attempt_log = []

        for provider in self.providers:
            # Skip unconfigured providers
            if not provider.is_configured():
                attempt_log.append(f"{provider.name}: NOT CONFIGURED")
                continue

            # Skip temporarily rate-limited providers
            if provider.is_rate_limited():
                attempt_log.append(f"{provider.name}: RATE LIMITED (Skipping)")
                continue

            keys = provider.get_api_keys()
            for key_idx, key in enumerate(keys):
                masked_k = mask_token(key)
                for model in provider.models:
                    logger.info(f"[AI Router] Trying: {provider.name} (Model: {model}, Key: {masked_k})...")
                    
                    for attempt in range(1, self.max_retries + 1):
                        try:
                            start_time = time.time()
                            output = self._call_provider(
                                provider, key, model, prompt, system_prompt,
                                max_tokens, temperature, json_mode, call_timeout
                            )
                            elapsed = round(time.time() - start_time, 2)
                            logger.info(f"[AI Router] Status: SUCCESS | Provider: {provider.name} | Model: {model} | Latency: {elapsed}s")
                            return output

                        except RuntimeError as e:
                            if "429" in str(e):
                                logger.warning(f"[AI Router] {provider.name}: RATE LIMITED (HTTP 429). Switching to next provider...")
                                attempt_log.append(f"{provider.name}: RATE LIMITED (429)")
                                break  # Break model retry, proceed to next key/provider
                            logger.warning(f"[AI Router] {provider.name} attempt {attempt} failed: {e}")
                            if attempt == self.max_retries:
                                attempt_log.append(f"{provider.name} ({model}): {e}")
                        
                        except PermissionError as e:
                            logger.warning(f"[AI Router] {provider.name}: AUTH FAILED ({masked_k}). Checking next key/provider...")
                            attempt_log.append(f"{provider.name}: AUTH ERROR")
                            break
                        
                        except LookupError as e:
                            logger.warning(f"[AI Router] {provider.name}: Model {model} unavailable, trying alternate model...")
                            break
                        
                        except requests.exceptions.Timeout:
                            logger.warning(f"[AI Router] {provider.name}: TIMEOUT (>{call_timeout}s). Switching to next provider...")
                            attempt_log.append(f"{provider.name}: TIMEOUT")
                            break
                        
                        except Exception as e:
                            logger.warning(f"[AI Router] {provider.name} error: {e}")
                            if attempt == self.max_retries:
                                attempt_log.append(f"{provider.name}: {e}")

                        # Exponential backoff delay for retries
                        if attempt < self.max_retries:
                            time.sleep(0.5 * (2 ** attempt))

        # If all providers fail, return a structured actionable error
        err_msg = (
            "All configured AI providers failed or were unavailable.\n"
            f"Attempt Trace: {' | '.join(attempt_log)}\n"
            "Please check your API keys in .env or your network connectivity."
        )
        logger.error(f"[AI Router] {err_msg}")
        raise RuntimeError(err_msg)


# ---------------------------------------------------------------------------
# Global Singleton Instance & Public API
# ---------------------------------------------------------------------------
_router_instance = AIRouter()

def generate_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    json_mode: bool = False,
    timeout: Optional[int] = None
) -> Union[str, Dict[str, Any]]:
    """
    Public Drop-In Function for DEMETER / DEM3T3R V1 / Any Project.
    
    Usage:
        from ai_router import generate_response
        answer = generate_response("Analyze this crop disease and give a recovery plan.")
        print(answer)
    """
    raw_response = _router_instance.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        json_mode=json_mode,
        timeout=timeout
    )
    if json_mode:
        try:
            return json.loads(raw_response)
        except Exception:
            return {"raw_response": raw_response}
    return raw_response


def get_router() -> AIRouter:
    """Access the underlying router instance."""
    return _router_instance
