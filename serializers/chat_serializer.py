import logging
from typing import Optional

# 최상위에 만든 exceptions.py에서 에러 클래스를 가져옵니다.
from exceptions import ChatSerializationError
from models.chat import ChatMessage

# 디버깅용 로거 생성
logger = logging.getLogger(__name__)


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
        except IndexError as e:
            # 리스트 인덱스 범위 초과 등 데이터 구조가 깨졌을 때 디버깅용 로그 남기기
            logger.warning(f"[ChatSerializer] 데이터 인덱스 파싱 실패 (요소 부족): {e}")
            raise ChatSerializationError(raw_data=data, message=f"인덱스 에러 ({e})")

        except Exception as e:
            # 그 외의 알 수 없는 치명적인 에러는 트레이스백 전체를 로그에 기록
            logger.error(
                "[ChatSerializer] 예기치 못한 데이터 복원 에러 발생", exc_info=True
            )
            raise ChatSerializationError(raw_data=data, message=str(e))
