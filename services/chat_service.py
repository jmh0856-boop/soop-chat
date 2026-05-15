import asyncio
import ssl
import threading
from typing import Callable, Optional, Set

import certifi
import httpx
import websockets

from models.chat import ChatMessage, Streamer
from serializers.chat_serializer import ChatSerializer
from storage.chat_storage import chat_storage

F = "\x0c"
ESC = "\x1b\t"


class ChatService:
    def __init__(self):
        self.active_streamers: Set[str] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._on_message_callback: Optional[Callable] = None

    def set_on_message(self, callback: Callable):
        self._on_message_callback = callback

    def start(self):
        print("채팅 수집기 시작!")
        self._loop = asyncio.new_event_loop()
        thread = threading.Thread(target=self._loop.run_forever)
        thread.daemon = True
        thread.start()

    def add_streamer(self, raw_input: str) -> str:
        streamer_id = self._extract_id(raw_input)
        if streamer_id in self.active_streamers:
            return f"{streamer_id} 는 이미 수집 중입니다"
        self.active_streamers.add(streamer_id)
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._connect_chat(streamer_id), self._loop
            )
        return f"{streamer_id} 채팅 수집 시작!"

    def remove_streamer(self, raw_input: str) -> str:
        streamer_id = self._extract_id(raw_input)
        if streamer_id in self.active_streamers:
            self.active_streamers.discard(streamer_id)
            chat_storage.clear(streamer_id)
            return f"{streamer_id} 수집 중단"
        return f"{streamer_id} 는 수집 중이 아닙니다"

    def stop_streamer(self, streamer_id: str) -> str:
        if streamer_id in self.active_streamers:
            self.active_streamers.discard(streamer_id)
            return f"{streamer_id} 수집 중단"
        return f"{streamer_id} 는 수집 중이 아닙니다"

    def _extract_id(self, text: str) -> str:
        text = text.strip()
        if "sooplive" in text or "afreecatv" in text:
            parts = text.rstrip("/").split("/")
            for part in reversed(parts):
                if (
                    part
                    and not part.isdigit()
                    and "sooplive" not in part
                    and "http" not in part
                ):
                    return part
        return text

    def _create_ssl_context(self):
        ssl_context = ssl.create_default_context()
        ssl_context.load_verify_locations(certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    def _calculate_byte_size(self, string: str) -> int:
        return len(string.encode("utf-8")) + 6

    async def get_bj_info(self, streamer_id: str) -> Optional[dict]:
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
                "chat_port": str(int(channel.get("CHPT")) + 1),
                "ft": channel.get("FTK"),
                "bjid": channel.get("BJID"),
                "bjnick": channel.get("BJNICK", ""),
                "chatno": channel.get("CHATNO"),
            }

    async def check_live(self, streamer_id: str) -> bool:
        info = await self.get_bj_info(streamer_id)
        return info is not None

    async def _connect_chat(self, streamer_id: str):
        print(f"{streamer_id} 방송 정보 가져오는 중...")
        info = await self.get_bj_info(streamer_id)
        if not info:
            print(f"{streamer_id} 방송 중이 아니거나 정보를 가져올 수 없어요")
            self.active_streamers.discard(streamer_id)
            return

        ssl_context = self._create_ssl_context()
        chat_url = (
            f"wss://{info['chat_ip']}:{info['chat_port']}/Websocket/{streamer_id}"
        )
        print(f"{streamer_id} 채팅 서버 연결 중... {chat_url}")

        CONNECT_PACKET = f"{ESC}000100000600{F*3}16{F}"
        JOIN_PACKET = f'{ESC}0002{self._calculate_byte_size(info["chatno"]):06}00{F}{info["chatno"]}{F*5}'
        PING_PACKET = f"{ESC}000000000100{F}"

        try:
            async with websockets.connect(
                chat_url,
                subprotocols=["chat"],
                ssl=ssl_context,
                ping_interval=None,
            ) as ws:
                await ws.send(CONNECT_PACKET)
                await asyncio.sleep(2)
                await ws.send(JOIN_PACKET)

                async def ping():
                    while True:
                        await asyncio.sleep(60)
                        if streamer_id not in self.active_streamers:
                            break
                        await ws.send(PING_PACKET)

                async def receive():
                    print(f"{streamer_id} 채팅 연결 성공!")
                    async for message in ws:
                        if streamer_id not in self.active_streamers:
                            break
                        if isinstance(message, bytes):
                            chat = ChatSerializer.deserialize(message, streamer_id)
                            if chat:
                                chat_storage.add(chat)
                                print(
                                    f"[{streamer_id}] {chat.nickname}({chat.user_id}): {chat.message}"
                                )
                                if self._on_message_callback:
                                    self._on_message_callback(chat)

                await asyncio.gather(receive(), ping())

        except Exception as e:
            self.active_streamers.discard(streamer_id)


chat_service = ChatService()
