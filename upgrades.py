from abc import ABC, abstractmethod
from datetime import datetime

from util import roman


class Upgrade(ABC):
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    @abstractmethod
    def get_cookies_since(self, timestamp: datetime, level: int) -> int:
        """ How many cookies given between `timestamp` and now, rounding DOWN
            to the nearest second """
        pass

    @abstractmethod
    def get_cookies_per_second(self, level: int) -> int:
        """ Cookies per second given by this upgrade at the given level """
        pass

    @abstractmethod
    def get_cookies_per_click(self, level: int) -> int:
        """ Cookies per click given by this upgrade at the given level """
        pass

    def get_cumulative_cookies_per_click(self, level: int) -> int:
        """ Cookies per click given by upgrades of every level up to and
            including `level` """
        return sum(self.get_cookies_per_click(n) for n in range(1, level + 1))

    def get_cumulative_cookies_per_second(self, level: int) -> int:
        """ Cookies per second given by upgrades of every level up to and
            including `level` """
        return sum(self.get_cookies_per_second(n) for n in range(1, level + 1))

    @abstractmethod
    def get_price(self, level: int) -> int:
        """ Price of the the upgrade at the given level """
        pass

class ClickUpgrade(Upgrade):
    def __init__(self, id, name, base_cpc: int):
        super().__init__(id, name)
        self.base_cpc = base_cpc

    def get_cookies_since(self, timestamp, level):
        return 0

    def get_cookies_per_second(self, level):
        return 0

    def get_cookies_per_click(self, level):
        return self.base_cpc * level

    def get_price(self, level):
        return 100

class PassiveUpgrade(Upgrade):
    def __init__(self, id: int, name, base_cps: int):
        super().__init__(id, name)
        self.base_cps = base_cps

    def get_cookies_since(self, timestamp, level):
        if self.base_cps == 0:
            return 0
        now = datetime.utcnow()
        delta = int((now - timestamp).total_seconds())
        return max(delta * self.get_cookies_per_second(level), 0)

    def get_cookies_per_second(self, level):
        return self.base_cps * level

    def get_cookies_per_click(self, level):
        return 0

    def get_price(self, level):
        return 100
