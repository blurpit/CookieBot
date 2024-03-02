import asyncio
import json
from datetime import datetime
from functools import wraps
from typing import Set

_1970 = datetime(1970, 1, 1).isoformat()


class Database:
    def __init__(self, filepath: str):
        self._filepath = filepath
        self._data: dict | None = None
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self.lock()
        self.load()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.save()
        self._data = None
        self.unlock()

    async def lock(self):
        await self._lock.acquire()

    def unlock(self):
        self._lock.release()

    def save(self):
        with open(self._filepath, 'w+') as f:
            f.write(json.dumps(self._data, indent=4))

    def load(self):
        with open(self._filepath, 'r') as f:
            self._data = json.loads(f.read() or '{}')

        self._data.setdefault('clicked_cookies', {})
        self._data.setdefault('last_clicked', _1970)
        self._data.setdefault('clicker_message_id', None)
        self._data.setdefault('clicker_channel_id', None)

    def get_clicker_message_id(self) -> int | None:
        return self._data['clicker_message_id']

    def get_clicker_channel_id(self) -> int | None:
        return self._data['clicker_channel_id']

    def set_clicker_message_id(self, message_id: int):
        self._data['clicker_message_id'] = message_id

    def set_clicker_channel_id(self, channel_id: int):
        self._data['clicker_channel_id'] = channel_id

    def get_cookies(self, user_id: int) -> int:
        return self.get_clicked_cookies(user_id)

    def get_total_cookies(self) -> int:
        return sum(self.get_cookies(user_id) for user_id in self.get_participants_user_ids())

    def get_clicked_cookies(self, user_id: int) -> int:
        return self._data['clicked_cookies'].get(str(user_id), 0)

    def add_clicked_cookies(self, user_id: int, cookies: int):
        if str(user_id) not in self._data['clicked_cookies']:
            self._data['clicked_cookies'] = 0
        self._data['clicked_cookies'][str(user_id)] += cookies

    def get_participants_user_ids(self) -> Set[int]:
        return set(map(int, self._data['clicked_cookies'].keys()))

    def get_last_clicked(self) -> datetime:
        return datetime.fromisoformat(self._data['last_clicked'])

    def update_last_clicked(self, timestamp: datetime = None) -> datetime:
        if timestamp is None:
            timestamp = datetime.utcnow()
        self._data['last_clicked'] = timestamp.isoformat()
        return timestamp

    def get_cooldown_remaining(self, cooldown: int) -> float:
        delta = datetime.utcnow() - self.get_last_clicked()
        return max(0.0, cooldown - delta.total_seconds())

    def is_on_cooldown(self, cooldown: int) -> bool:
        return self.get_cooldown_remaining(cooldown) > 0
