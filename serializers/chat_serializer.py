from typing import Optional

from models.chat import ChatMessage


class ChatSerializer:
    @staticmethod
    def deserialize(data: bytes, streamer_id: str) -> Optional[ChatMessage]:
        try:
            parts = data.split(b"\x0c")
            messages = [part.decode("utf-8", errors="ignore") for part in parts]
            if not messages:
                return None
            header = messages[0]
            if "0005" not in header and "00050" not in header:
                return None
            if "0127" in header or "12700" in header:
                return None
            if len(messages) < 7:
                return None
            comment = messages[1]
            user_id = messages[2]
            user_nickname = messages[6]
            if not comment or not user_nickname:
                return None
            if "|" in user_nickname or user_nickname == "-1":
                return None
            return ChatMessage(
                streamer_id=streamer_id,
                nickname=user_nickname,
                user_id=user_id,
                message=comment,
            )
        except Exception:
            return None
