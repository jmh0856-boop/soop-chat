import asyncio
from typing import List

from services.chat_service import chat_service
from storage.chat_storage import favorite_storage


class FavoriteService:
    def get_all(self) -> List[str]:
        return favorite_storage.get_all()

    def get_id(self, display: str) -> str:
        return favorite_storage.get_id(display)

    def remove(self, display_or_id: str):
        favorite_storage.remove(display_or_id)

    def add(self, streamer_id: str):
        async def get_nick():
            info = await chat_service.get_bj_info(streamer_id)
            return info.get("bjnick", "") if info else ""

        try:
            loop = asyncio.new_event_loop()
            nickname = loop.run_until_complete(get_nick())
            loop.close()
        except Exception:
            nickname = ""

        favorite_storage.add(streamer_id, nickname)

    def is_favorite(self, streamer_id: str) -> bool:
        return streamer_id in favorite_storage.favorites


favorite_service = FavoriteService()
