from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    title: str
    link: str
    summary: str
    source: str
    published_time: datetime
    category: Optional[str] = None
    ai_summary: Optional[str] = None
    importance: Optional[int] = None
    tags: Optional[list[str]] = None

