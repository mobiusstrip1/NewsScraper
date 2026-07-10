import logging
import os
from pathlib import Path

from dotenv import load_dotenv


def load_project_env() -> Path:
    root = Path(__file__).resolve().parents[1]
    env_path = root / '.env'
    load_dotenv(env_path)
    return env_path


def mask_secret(value: str) -> str:
    value = (value or '').strip()
    if not value:
        return '(empty)'
    if len(value) <= 8:
        return '(too short)'
    return f'{value[:4]}...{value[-4:]}'


def validate_env() -> None:
    bark_key = os.getenv('BARK_KEY', '').strip()
    if not bark_key:
        logging.warning(
            'BARK_KEY is empty. Check .env has only one BARK_KEY line with your Bark homepage Key.'
        )
    else:
        logging.info('BARK_KEY loaded: %s', mask_secret(bark_key))

    llm_provider = os.getenv('LLM_PROVIDER', 'auto')
    if os.getenv('OPENAI_API_KEY', '').strip() or os.getenv('ANTHROPIC_API_KEY', '').strip():
        model = os.getenv('OPENAI_MODEL', os.getenv('CLAUDE_MODEL', ''))
        logging.info(
            'LLM provider=%s model=%s classify_timeout=%ss polish_timeout=%ss workers=%s',
            llm_provider,
            model,
            os.getenv('LLM_TIMEOUT_CLASSIFY', '600'),
            os.getenv('LLM_TIMEOUT_POLISH', '600'),
            os.getenv('LLM_CLASSIFY_WORKERS', '3'),
        )
    else:
        logging.warning('No LLM API key found. Classification will use fallback rules only.')
