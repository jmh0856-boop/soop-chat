from typing import Callable, List, Optional

from services.chat_service import chat_service
from services.favorite_service import favorite_service
from storage.chat_storage import chat_storage


class MainViewModel:
    def __init__(self):
        self.on_chat_updated: Optional[Callable] = None

    def start(self):
        chat_service.set_on_message(self._on_new_message)
        chat_service.start()

    def _on_new_message(self, chat):
        if self.on_chat_updated:
            self.on_chat_updated()

    # 스트리머
    def add_streamer(self, raw_input: str) -> str:
        return chat_service.add_streamer(raw_input)

    def remove_streamer(self, raw_input: str) -> str:
        return chat_service.remove_streamer(raw_input)

    def get_active_streamers(self) -> List[str]:
        return list(chat_service.active_streamers)

    # 채팅
    def get_all_chats(self, streamer_id: str) -> List[dict]:
        return chat_storage.get_all(streamer_id)

    def search_by_nickname(self, streamer_id: str, nickname: str) -> List[dict]:
        return chat_storage.search_by_nickname(streamer_id, nickname)

    # 즐겨찾기
    def get_favorites(self) -> List[str]:
        return favorite_service.get_all()

    def toggle_favorite(self, streamer_id: str):
        if favorite_service.is_favorite(streamer_id):
            favorite_service.remove(streamer_id)
        else:
            favorite_service.add(streamer_id)

    def get_favorite_id(self, display: str) -> str:
        return favorite_service.get_id(display)

    def remove_favorite(self, display: str):
        favorite_service.remove(display)

    def extract_id(self, text: str) -> str:
        return chat_service._extract_id(text)

    # 탭
    def stop_streamer(self, streamer_id: str) -> str:
        return chat_service.stop_streamer(streamer_id)

    def is_live(self, streamer_id: str) -> bool:
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(chat_service.check_live(streamer_id))
            loop.close()
            return result
        except:
            return False


main_viewmodel = MainViewModel()
