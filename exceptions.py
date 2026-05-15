# exceptions.py


class SoopChatError(Exception):
    """soop-chat 프로젝트의 최상위 기본 예외 클래스"""

    def __init__(self, message: str = "SOOP 채팅 앱 내부 오류가 발생했습니다."):
        self.message = message
        super().__init__(self.message)


class ChatSerializationError(SoopChatError):
    """채팅 데이터를 파싱(deserialize)하거나 변환할 때 발생하는 예외"""

    def __init__(self, raw_data, message: str = "채팅 데이터 파싱에 실패했습니다."):
        self.raw_data = raw_data
        self.message = f"{message} | 원본 데이터: {raw_data}"
        super().__init__(self.message)


class NetworkConnectionError(SoopChatError):
    """웹소켓 또는 API 연결이 끊기거나 실패했을 때 발생하는 예외"""

    def __init__(
        self, target_url: str, message: str = "서버와의 연결이 원활하지 않습니다."
    ):
        self.target_url = target_url
        self.message = f"{message} (대상 주소: {target_url})"
        super().__init__(self.message)


class ReconnectionMaxResultError(NetworkConnectionError):
    """지정한 최대 재연결 시도 횟수를 초과했을 때 발생하는 예외"""

    def __init__(self, target_url: str, attempts: int):
        self.attempts = attempts
        error_message = (
            f"최대 재연결 시도 횟수({attempts}회)를 초과하여 연결을 포기합니다."
        )
        super().__init__(target_url=target_url, message=error_message)
