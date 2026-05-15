import json
from collections import defaultdict
from typing import Dict, List, Optional

from models.chat import ChatMessage


class ChatStorage:
    def __init__(self):
        self.data: Dict[str, Dict[str, List[dict]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def add(self, message: ChatMessage):
        self.data[message.streamer_id][message.nickname].append(
            {
                "nickname": message.nickname,
                "user_id": message.user_id,
                "message": message.message,
                "time": message.timestamp,
            }
        )

    def search_by_nickname(self, streamer_id: str, nickname: str) -> List[dict]:
        result = []
        streamer_data = self.data.get(streamer_id, {})
        for nick, chats in streamer_data.items():
            if nickname.lower() in nick.lower():
                result.extend(chats)
        result.sort(key=lambda x: x["time"])
        return result

    def get_all(self, streamer_id: str) -> List[dict]:
        result = []
        streamer_data = self.data.get(streamer_id, {})
        for chats in streamer_data.values():
            result.extend(chats)
        result.sort(key=lambda x: x["time"])
        return result

    def get_streamers(self) -> List[str]:
        return list(self.data.keys())

    def clear(self, streamer_id: str):
        if streamer_id in self.data:
            del self.data[streamer_id]


class FavoriteStorage:
    def __init__(self):
        self.favorites: Dict[str, str] = {}
        self._load()

    def _load(self):
        try:
            with open("favorites.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.favorites = {k: k for k in data}
                else:
                    self.favorites = data
        except Exception:
            self.favorites = {}

    def _save(self):
        with open("favorites.json", "w", encoding="utf-8") as f:
            json.dump(self.favorites, f, ensure_ascii=False)

    def add(self, streamer_id: str, nickname: str = ""):
        display = f"{nickname}({streamer_id})" if nickname else streamer_id
        self.favorites[streamer_id] = display
        self._save()

    def remove(self, display_or_id: str):
        if display_or_id in self.favorites:
            del self.favorites[display_or_id]
            self._save()
            return
        for k, v in list(self.favorites.items()):
            if v == display_or_id:
                del self.favorites[k]
                self._save()
                return

    def get_all(self) -> List[str]:
        return list(self.favorites.values())

    def get_id(self, display: str) -> str:
        for k, v in self.favorites.items():
            if v == display:
                return k
        return display


chat_storage = ChatStorage()
favorite_storage = FavoriteStorage()
