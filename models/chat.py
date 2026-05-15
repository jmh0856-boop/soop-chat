import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChatMessage:
    streamer_id: str
    nickname: str
    user_id: str
    message: str
    timestamp: str = field(default_factory=lambda: time.strftime("%H:%M:%S"))


@dataclass
class Streamer:
    streamer_id: str
    nickname: str = ""
    is_active: bool = False
