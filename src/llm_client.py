import logging
import os

import requests
from anthropic import Anthropic


class LLMClient:
    def __init__(self) -> None:
        provider = os.getenv('LLM_PROVIDER', 'auto').strip().lower()
        self.provider = self._resolve_provider(provider)

        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
        self.anthropic_model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5').strip()

        self.openai_key = os.getenv('OPENAI_API_KEY', '').strip()
        self.openai_model = os.getenv('OPENAI_MODEL', 'qwen3.5-flash').strip()
        self.openai_model_classify = os.getenv('OPENAI_MODEL_CLASSIFY', self.openai_model).strip()
        self.openai_model_polish = os.getenv('OPENAI_MODEL_POLISH', self.openai_model).strip()
        self.openai_base_url = os.getenv(
            'OPENAI_BASE_URL',
            'https://dashscope.aliyuncs.com/compatible-mode/v1',
        ).strip().rstrip('/')

        self.default_timeout = int(os.getenv('LLM_TIMEOUT', '600'))
        self.classify_timeout = int(os.getenv('LLM_TIMEOUT_CLASSIFY', '600'))
        self.polish_timeout = int(os.getenv('LLM_TIMEOUT_POLISH', '600'))

        self.client = (
            Anthropic(api_key=self.anthropic_key)
            if self.provider == 'anthropic' and self.anthropic_key
            else None
        )

    def _resolve_provider(self, provider: str) -> str:
        if provider in ('anthropic', 'openai_compatible'):
            return provider
        if os.getenv('OPENAI_API_KEY', '').strip():
            return 'openai_compatible'
        if os.getenv('ANTHROPIC_API_KEY', '').strip():
            return 'anthropic'
        return 'fallback'

    @property
    def available(self) -> bool:
        return self.provider != 'fallback'

    def chat(
        self,
        prompt: str,
        *,
        max_tokens: int = 2000,
        timeout: int | None = None,
        model: str | None = None,
        purpose: str = 'default',
    ) -> str | None:
        if self.provider == 'anthropic' and self.client:
            response = self.client.messages.create(
                model=model or self.anthropic_model,
                max_tokens=max_tokens,
                temperature=0,
                messages=[{'role': 'user', 'content': prompt}],
            )
            return ''.join(
                block.text for block in response.content if getattr(block, 'text', None)
            ).strip()

        if self.provider == 'openai_compatible' and self.openai_key:
            if purpose == 'classify':
                req_timeout = timeout or self.classify_timeout
                req_model = model or self.openai_model_classify
            elif purpose == 'polish':
                req_timeout = timeout or self.polish_timeout
                req_model = model or self.openai_model_polish
            else:
                req_timeout = timeout or self.default_timeout
                req_model = model or self.openai_model

            logging.debug('LLM call purpose=%s model=%s timeout=%ss', purpose, req_model, req_timeout)
            resp = requests.post(
                f'{self.openai_base_url}/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': req_model,
                    'temperature': 0,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': max_tokens,
                },
                timeout=req_timeout,
            )
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content'].strip()

        return None
