import json
import asyncio
from typing import Optional, Any
from urllib.parse import urlparse

from aiohttp import ClientSession, WSMsgType


class Conn:
    # receive_timeout 推荐为heartbeat间隔加10/5
    def __init__(self, receive_timeout: Optional[float] = None):
        self._receive_timeout = receive_timeout

    async def open(self) -> bool:
        return False

    async def close(self) -> bool:
        return True

    # 用于永久close之后一些数据清理等
    async def clean(self):
        pass

    async def send_bytes(self, bytes_data) -> bool:
        return True

    async def read_bytes(self) -> Optional[bytes]:
        return None

    async def read_json(self) -> Any:
        return None


class WsConn(Conn):
    # url 格式 ws://hostname:port/… 或者 wss://hostname:port/…
    def __init__(
            self, url: str,
            receive_timeout: Optional[float] = None,
            session: Optional[ClientSession] = None,
            ws_receive_timeout: Optional[float] = None,  # 自动pingpong时候用的
            ws_heartbeat: Optional[float] = None):  # 自动pingpong时候用的
        super().__init__(receive_timeout)
        result = urlparse(url)
        assert result.scheme == 'ws' or result.scheme == 'wss'
        self._url = url

        if session is None:
            self._is_sharing_session = False
            self._session = ClientSession()
        else:
            self._is_sharing_session = True
            self._session = session
        self._ws_receive_timeout = ws_receive_timeout
        self._ws_heartbeat = ws_heartbeat
        self._ws = None

    async def open(self) -> bool:
        try:
            self._ws = await asyncio.wait_for(
                self._session.ws_connect(
                    self._url,
                    receive_timeout=self._ws_receive_timeout,
                    heartbeat=self._ws_heartbeat), timeout=3)
        except asyncio.TimeoutError:
            return False
        except Exception:
            return False
        return True

    async def close(self) -> bool:
        if self._ws is not None:
            await self._ws.close()
        return True

    async def clean(self):
        if not self._is_sharing_session:
            await self._session.close()

    async def send_bytes(self, bytes_data) -> bool:
        try:
            await self._ws.send_bytes(bytes_data)
        except asyncio.CancelledError:
            return False
        except Exception:
            return False
        return True

    async def read_bytes(self) -> Optional[bytes]:
        try:
            bytes_data = await asyncio.wait_for(
                self._ws.receive_bytes(), timeout=self._receive_timeout)
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

        return bytes_data

    async def read_json(self) -> Any:
        try:
            msg = await asyncio.wait_for(
                self._ws.receive(), timeout=self._receive_timeout)
            if msg.type == WSMsgType.TEXT:
                return json.loads(msg.data)
            elif msg.type == WSMsgType.BINARY:
                return json.loads(msg.data.decode('utf8'))
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

        return None
