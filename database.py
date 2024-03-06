import asyncio
import json
from datetime import datetime

from config import UPGRADES
from upgrades import ClickUpgrade, PassiveUpgrade

_1970 = datetime(1970, 1, 1).isoformat()


class Database:
    def __init__(self, filepath: str):
        self._filepath = filepath
        self._data: dict | None = None
        self._lock = asyncio.Lock()

    # --- IO --- #

    async def __aenter__(self):
        if self._data is None: # ignore nested withs
            await self._lock.acquire()
            self.load()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._data is not None:
            self.save()
            self._data = None
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
        self._data.setdefault('upgrade_message_owner_ids', {})
        self._data.setdefault('last_clicked_time', _1970)
        self._data.setdefault('last_clicked_user_id', None)
        self._data.setdefault('last_clicked_value', 0)

    # --- Message storage --- #
    def get_clicker_message_id(self) -> int | None:
        """ ID of the message with the cookie button and leaderboard """
        return self._data['clicker_message_id']

    def get_clicker_channel_id(self) -> int | None:
        """ ID of the channel the clicker message is in """
        return self._data['clicker_channel_id']

    def set_clicker_message_id(self, message_id: int | None):
        """ Set the clicker message id """
        self._data['clicker_message_id'] = message_id

    def set_clicker_channel_id(self, channel_id: int | None):
        """ Set the clicker channel id """
        self._data['clicker_channel_id'] = channel_id

    def get_upgrade_message_owner_id(self, message_id: int) -> int | None:
        """ ID of the user who owns the given upgrade message """
        return self._data['upgrade_message_owner_ids'].get(str(message_id), None)

    def set_upgrade_message_owner_id(self, message_id: int | None, user_id: int):
        """ Set the owner of the given upgrade message """
        self._data['upgrade_message_owner_ids'][str(message_id)] = user_id

    # --- Cookie counts --- #

    def get_total_cookies(self) -> int:
        """ Total number of cookies everyone collectively has """
        return sum(
            self.get_cookies(user_id)
            for user_id in self.get_participants_user_ids()
        )

    def get_cookies(self, user_id: int) -> int:
        """ Number of cookies a given user has """
        return self._data['cookies'].get(str(user_id), 0)

    def set_cookies(self, user_id: int, cookies: int):
        """ Sets the cookie count for a given user """
        self._data['cookies'][str(user_id)] = cookies

    def add_cookies(self, user_id: int, cookies: int):
        """ Adds cookies to a given user's count """
        self.set_cookies(user_id, self.get_cookies(user_id) + cookies)

    def delete_participant(self, user_id: int):
        self._data['cookies'].pop(str(user_id), None)
        self._data['upgrades'].pop(str(user_id), None)
        if user_id == self._data['last_clicked_user_id']:
            self._data['last_clicked_user_id'] = None
            self._data['last_clicked_value'] = 0

    # --- Upgrades --- #

    def get_upgrade_levels(self, user_id: int) -> list[int]:
        """ Returns a list of levels for the upgrades the given user owns (indices
            match config.UPGRADES) """
        levels = [0] * len(UPGRADES)
        for id, level in self._data['upgrades'].get(str(user_id), {}).items():
            levels[int(id)] = level
        return levels

    def get_upgrade_level(self, user_id: int, upgrade_id: int) -> int:
        """ Level of a specific upgrade """
        return self._data['upgrades'].get(str(user_id), {}).get(str(upgrade_id), 0)

    def get_cookies_per_second(self, user_id: int) -> int:
        """ Number of cookies a given user gets each second through passive upgrades """
        return sum(
            UPGRADES[i].get_cookies_per_unit(level)
            for i, level in enumerate(self.get_upgrade_levels(user_id))
            if isinstance(UPGRADES[i], PassiveUpgrade)
        )

    def get_cookies_per_click(self, user_id: int) -> int:
        """ Number of cookies a given user gets from clicking due to upgrades.
            Does not include the base number of cookies the button gives. """
        return sum(
            UPGRADES[i].get_cookies_per_unit(level)
            for i, level in enumerate(self.get_upgrade_levels(user_id))
            if isinstance(UPGRADES[i], ClickUpgrade)
        )

    def get_spent_on_upgrades(self, user_id: int) -> int:
        """ How many cookies a given user has spent on upgrades """
        return sum(
            UPGRADES[i].get_price(level)
            for i, level in enumerate(self.get_upgrade_levels(user_id))
        )

    def set_upgrade_level(self, user_id: int, upgrade_id: int, level: int):
        """ Sets the level of an upgrade for a given user """
        if str(user_id) not in self._data['upgrades']:
            self._data['upgrades'][str(user_id)] = {}
        self._data['upgrades'][str(user_id)][str(upgrade_id)] = level

    def does_someone_own(self, upgrade_id: int):
        """ True if anyone has purchased the given upgrade """
        for purchases in self._data['upgrades'].values():
            if str(upgrade_id) in purchases:
                return True
        return False

    # --- Clicker state --- #

    def get_participants_user_ids(self) -> list[int]:
        """ Set of user_ids of people who have clicked the button before """
        return list(map(int, self._data['cookies'].keys()))

    def get_last_clicked_time(self) -> datetime:
        """ Timestamp of when the button was last clicked by someone """
        return datetime.fromisoformat(self._data['last_clicked_time'])

    def set_last_clicked_time(self, timestamp: datetime = None) -> datetime:
        """ Set the timestamp of when the button was last clicked """
        if timestamp is None:
            timestamp = datetime.utcnow()
        self._data['last_clicked_time'] = timestamp.isoformat()
        return timestamp

    def get_last_clicked_user_id(self) -> int | None:
        """ User id of the person who last clicked the button """
        return self._data['last_clicked_user_id']

    def set_last_clicked_user_id(self, user_id: int | None):
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
