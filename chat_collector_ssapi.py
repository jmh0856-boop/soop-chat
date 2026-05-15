import threading

import socketio

from storage import storage

SSAPI_URL = "https://socket.ssapi.kr"
API_KEY = "YOUR_API_KEY"

active_streamers = set()

sio = socketio.Client()


@sio.event
def connect():
    print("SSAPI 연결 성공!")
    sio.emit("login", {"apiKey": API_KEY})


@sio.event
def disconnect():
    print("SSAPI 연결 끊김")


@sio.on("chat")
def on_chat(data):
    try:
        streamer_id = data.get("streamerId", "")
        nickname = data.get("nickname", "알수없음")
        message = data.get("message", "")
        if streamer_id and message:
            storage.add_chat(streamer_id, nickname, message)
            print(f"[{streamer_id}] {nickname}: {message}")
    except Exception as e:
        print(f"채팅 처리 오류: {e}")


def add_streamer(streamer_id):
    if streamer_id in active_streamers:
        return f"{streamer_id} 는 이미 수집 중입니다"
    active_streamers.add(streamer_id)
    if sio.connected:
        sio.emit("join", {"streamerId": streamer_id, "platform": "afreeca"})
        return f"{streamer_id} 채팅 수집 시작!"
    return "SSAPI 연결 중... 잠시 후 다시 시도해주세요"


def remove_streamer(streamer_id):
    if streamer_id in active_streamers:
        active_streamers.discard(streamer_id)
        if sio.connected:
            sio.emit("leave", {"streamerId": streamer_id, "platform": "afreeca"})
        return f"{streamer_id} 수집 중단"
    return f"{streamer_id} 는 수집 중이 아닙니다"


def start():
    def run():
        try:
            sio.connect(SSAPI_URL)
            sio.wait()
        except Exception as e:
            print(f"연결 오류: {e}")

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    print("채팅 수집기 시작!")
