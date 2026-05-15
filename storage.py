import time
from collections import defaultdict


class ChatStorage:
    def __init__(self):
        # 방송별로 채팅 저장
        # 구조: { 스트리머ID: { 닉네임: [ 채팅목록 ] } }
        self.data = defaultdict(lambda: defaultdict(list))

    def add_chat(self, streamer_id, nickname, message, user_id=""):
        chat = {
            "nickname": nickname,
            "user_id": user_id,
            "message": message,
            "time": time.strftime("%H:%M:%S"),
        }
        self.data[streamer_id][nickname].append(chat)

    def search_by_nickname(self, streamer_id, nickname):
        # 닉네임으로 채팅 검색 (부분 일치)
        result = []
        streamer_data = self.data.get(streamer_id, {})
        for nick, chats in streamer_data.items():
            if nickname.lower() in nick.lower():
                result.extend(chats)
        # 시간순 정렬
        result.sort(key=lambda x: x["time"])
        return result

    def get_all_chats(self, streamer_id):
        # 특정 방송 전체 채팅
        result = []
        streamer_data = self.data.get(streamer_id, {})
        for chats in streamer_data.values():
            result.extend(chats)
        result.sort(key=lambda x: x["time"])
        return result

    def get_streamers(self):
        # 현재 수집 중인 방송 목록
        return list(self.data.keys())

    def clear(self, streamer_id):
        # 특정 방송 채팅 초기화
        if streamer_id in self.data:
            del self.data[streamer_id]


# 앱 전체에서 하나만 사용
storage = ChatStorage()
