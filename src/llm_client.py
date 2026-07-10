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
        self.openai_model = os.getenv('OPENAI_MODEL', 'qwen-plus').strip()
        self.openai_base_url = os.getenv(
            'OPENAI_BASE_URL',
            'https://dashscope.aliyuncs.com/compatible-mode/v1',
        ).strip().rstrip('/')

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

    def chat(self, prompt: str, *, max_tokens: int = 2000) -> str | None:
        if self.provider == 'anthropic' and self.client:
            response = self.client.messages.create(
                model=self.anthropic_model,
                max_tokens=max_tokens,
                temperature=0,
                messages=[{'role': 'user', 'content': prompt}],
            )
            return ''.join(
                block.text for block in response.content if getattr(block, 'text', None)
            ).strip()

        if self.provider == 'openai_compatible' and self.openai_key:
            resp = requests.post(
                f'{self.openai_base_url}/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': self.openai_model,
                    'temperature': 0,
                    'messages': [{'role': 'user', 'content': prompt}],
                },
                timeout=90,
            )
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content'].strip()

        return None
