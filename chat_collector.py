import asyncio
import ssl
import threading

import certifi
import httpx
import websockets

from storage import storage

active_streamers = set()
_loop = None

F = "\x0c"
ESC = "\x1b\t"


def create_ssl_context():
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations(certifi.where())
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


def calculate_byte_size(string):
    return len(string.encode("utf-8")) + 6


async def get_bj_info(streamer_id: str):
    url = "https://live.sooplive.co.kr/afreeca/player_live_api.php"
    data = {
        "bid": streamer_id,
        "type": "live",
        "quality": "master",
        "cmd": 10019,
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(url, data=data)
        result = res.json()
        channel = result.get("CHANNEL", {})
        if channel.get("RESULT") != 1:
            return None
        return {
            "bno": channel.get("BNO"),
            "chat_ip": channel.get("CHDOMAIN").lower(),
            "chat_port": str(int(channel.get("CHPT")) + 1),  # +1 추가!
            "ft": channel.get("FTK"),
            "bjid": channel.get("BJID"),
            "chatno": channel.get("CHATNO"),
        }


def decode_message(data, streamer_id):
    try:
        parts = data.split(b"\x0c")
        messages = [part.decode("utf-8", errors="ignore") for part in parts]
        if not messages:
            return
        header = messages[0]
        if "0005" not in header:
            return
        if len(messages) < 7:
            return
        comment = messages[1]
        user_id = messages[2]
        user_nickname = messages[6]
        if not comment or not user_nickname:
            return
        if "|" in user_nickname or user_nickname == "-1":
            return
        storage.add_chat(streamer_id, user_nickname, comment, user_id)
        print(f"[{streamer_id}] {user_nickname}({user_id}): {comment}")
    except Exception as e:
        pass


async def connect_chat(streamer_id: str):
    print(f"{streamer_id} 방송 정보 가져오는 중...")
    info = await get_bj_info(streamer_id)

    if not info:
        print(f"{streamer_id} 방송 중이 아니거나 정보를 가져올 수 없어요")
        active_streamers.discard(streamer_id)
        return

    ssl_context = create_ssl_context()
    chat_url = f"wss://{info['chat_ip']}:{info['chat_port']}/Websocket/{streamer_id}"
    print(f"{streamer_id} 채팅 서버 연결 중... {chat_url}")

    CONNECT_PACKET = f"{ESC}000100000600{F*3}16{F}"
    JOIN_PACKET = (
        f'{ESC}0002{calculate_byte_size(info["chatno"]):06}00{F}{info["chatno"]}{F*5}'
    )
    PING_PACKET = f"{ESC}000000000100{F}"

    try:
        async with websockets.connect(
            chat_url, subprotocols=["chat"], ssl=ssl_context, ping_interval=None
        ) as ws:
            print(f"{streamer_id} 채팅 연결 성공!")

            await ws.send(CONNECT_PACKET)
            print(f"{streamer_id} CONNECT 패킷 전송")
            await asyncio.sleep(2)

            await ws.send(JOIN_PACKET)
            print(f"{streamer_id} JOIN 패킷 전송")

            async def ping():
                while True:
                    await asyncio.sleep(60)
                    if streamer_id not in active_streamers:
                        break
                    await ws.send(PING_PACKET)

            async def receive():
                async for message in ws:
                    if streamer_id not in active_streamers:
                        break
                    if isinstance(message, bytes):
                        decode_message(message, streamer_id)

            await asyncio.gather(receive(), ping())

    except Exception as e:
        print(f"{streamer_id} 연결 오류: {e}")
        active_streamers.discard(streamer_id)


def add_streamer(raw_input):
    streamer_id = raw_input.strip()
    if "sooplive" in streamer_id or "afreecatv" in streamer_id:
        parts = streamer_id.rstrip("/").split("/")
        streamer_id = parts[-2] if len(parts) > 1 else parts[-1]

    if streamer_id in active_streamers:
        return f"{streamer_id} 는 이미 수집 중입니다"
    active_streamers.add(streamer_id)
    if _loop:
        asyncio.run_coroutine_threadsafe(connect_chat(streamer_id), _loop)
    return f"{streamer_id} 채팅 수집 시작!"


def remove_streamer(streamer_id):
    if streamer_id in active_streamers:
        active_streamers.discard(streamer_id)
        return f"{streamer_id} 수집 중단"
    return f"{streamer_id} 는 수집 중이 아닙니다"


def start():
    global _loop
    _loop = asyncio.new_event_loop()
    thread = threading.Thread(target=_loop.run_forever)
    thread.daemon = True
    thread.start()
    print("채팅 수집기 시작!")
