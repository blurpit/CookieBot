import asyncio
import json
from datetime import datetime
from typing import Iterable, Set

from config import UPGRADES
from upgrades import Upgrade

_1970 = datetime(1970, 1, 1).isoformat()


class Database:
    def __init__(self, filepath: str):
        self._filepath = filepath
        self._data: dict | None = None
        self._lock = asyncio.Lock()

    # --- IO --- #

    async def __aenter__(self):
        await self.lock()
        self.load()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.save()
        self._data = None
        self.unlock()

    async def lock(self):
        """ Threadlock the database """
        await self._lock.acquire()

    def unlock(self):
        """ Release the database lock """
        self._lock.release()

    def save(self):
        """ Save the database to the file """
        with open(self._filepath, 'w+') as f:
            f.write(json.dumps(self._data, indent=4))

    def load(self):
        """ Load the database from the file """
        with open(self._filepath, 'r') as f:
            self._data = json.loads(f.read() or '{}')

        self._data.setdefault('clicked_cookies', {})
        self._data.setdefault('upgrades', {})
        self._data.setdefault('clicker_message_id', None)
        self._data.setdefault('clicker_channel_id', None)
        self._data.setdefault('last_clicked_time', _1970)
        self._data.setdefault('last_clicked_user_id', None)
        self._data.setdefault('last_clicked_value', 0)

    # --- Clicker message --- #
    def get_clicker_message_id(self) -> int | None:
        """ ID of the message with the cookie button and leaderboard """
        return self._data['clicker_message_id']

    def get_clicker_channel_id(self) -> int | None:
        """ ID of the channel the clicker message is in """
        return self._data['clicker_channel_id']

    def set_clicker_message_id(self, message_id: int):
        """ Set the clicker message id """
        self._data['clicker_message_id'] = message_id

    def set_clicker_channel_id(self, channel_id: int):
        """ Set the clicker channel id """
        self._data['clicker_channel_id'] = channel_id

    # --- Cookie counts --- #

    def get_total_cookies(self) -> int:
        """ Total number of cookies everyone collectively has """
        return sum(
            self.get_cookies(user_id)
            for user_id in self.get_participants_user_ids()
        )

    def get_cookies(self, user_id: int) -> int:
        """ Number of cookies a given user has """
        return (self.get_clicked_cookies(user_id)
                + self.get_passive_cookies(user_id)
                - self.get_spent_on_upgrades(user_id))

    def get_clicked_cookies(self, user_id: int) -> int:
        """ Number of cookies a given user has gotten through clicking the button """
        return self._data['clicked_cookies'].get(str(user_id), 0)

    def get_passive_cookies(self, user_id: int) -> int:
        """ Number of cookies a given user has gotten through passive upgrades """
        return sum(
            upgrade.get_cookies_since(purchased, level)
            for upgrade, level, purchased in self.iter_upgrades(user_id)
        )

    def add_clicked_cookies(self, user_id: int, cookies: int):
        """ Adds a number of cookies to a given user's clicked cookies count """
        if str(user_id) not in self._data['clicked_cookies']:
            self._data['clicked_cookies'] = 0
        self._data['clicked_cookies'][str(user_id)] += cookies

    # --- Upgrades --- #

    def iter_upgrades(self, user_id: int) -> Iterable[tuple[Upgrade, int, datetime]]:
        """ Iterates the upgrades a given user has purchased. Yields
            (Upgrade, level, purchased timestamp) """
        copies = {}
        for upgrade in self._data['upgrades'].get(str(user_id), []):
            id = upgrade['id']
            copies[id] = copies.get(id, 0) + 1
            purchased = datetime.fromisoformat(upgrade['purchased'])
            yield UPGRADES[id], copies[id], purchased

    def get_highest_upgrades(self, user_id: int) -> dict[int, tuple[int, datetime]]:
        """ Returns a dict of upgrade id -> highest level, last purchased """
        result = {}

        for upgrade in self._data['upgrades'].get(str(user_id), []):
            id = upgrade['id']
            purchased = datetime.fromisoformat(upgrade['purchased'])
            level = 0
            if id in result:
                level = result[id][0]
            result[id] = (level + 1, purchased)

        return result

    def get_cookies_per_second(self, user_id: int) -> int:
        """ Number of cookies a given user gets each second through passive upgrades """
        return sum(
            upgrade.get_cookies_per_second(level)
            for upgrade, level, _ in self.iter_upgrades(user_id)
        )

    def get_cookies_per_click(self, user_id: int) -> int:
        """ Number of cookies a given user gets from clicking due to upgrades.
            Does not include the base number of cookies the button gives. """
        return sum(
            upgrade.get_cookies_per_click(level)
            for upgrade, level, _ in self.iter_upgrades(user_id)
        )

    def get_spent_on_upgrades(self, user_id: int) -> int:
        """ How many cookies a given user has spent on upgrades """
        return sum(
            upgrade.get_price(level)
            for upgrade, level, _ in self.iter_upgrades(user_id)
        )

    # --- Clicker state --- #

    def get_participants_user_ids(self) -> Set[int]:
        """ Set of user_ids of people who have clicked the button before """
        return set(map(int, self._data['clicked_cookies'].keys()))

    def get_last_clicked_time(self) -> datetime:
        """ Timestamp of when the button was last clicked by someone """
        return datetime.fromisoformat(self._data['last_clicked_time'])

    def update_last_clicked(self, timestamp: datetime = None) -> datetime:
        """ Set the timestamp of when the button was last clicked """
        if timestamp is None:
            timestamp = datetime.utcnow()
        self._data['last_clicked_time'] = timestamp.isoformat()
        return timestamp

    def get_last_clicked_user_id(self) -> int | None:
        """ User id of the person who last clicked the button """
        return self._data['last_clicked_user_id']

    def set_last_clicked_user_id(self, user_id: int):
        """ Set the user id of the person who last clicked the button """
        self._data['last_clicked_user_id'] = user_id

    def get_last_clicked_value(self) -> int:
        """ How many cookies the last button click gave """
        return self._data['last_clicked_value']

    def set_last_clicked_value(self, cookies: int):
        """ Set how many cookies the last button click gave """
        self._data['last_clicked_value'] = cookies

    def get_cooldown_remaining(self, cooldown: int) -> float:
        """ Seconds remaining in seconds on the button cooldown (given the total
            cooldown time in seconds) """
        delta = datetime.utcnow() - self.get_last_clicked_time()
        return max(0.0, cooldown - delta.total_seconds())

    def is_on_cooldown(self, cooldown: int) -> bool:
        """ Whether the button is on cooldown (given the total cooldown time in
            seconds) """
        return self.get_cooldown_remaining(cooldown) > 0
