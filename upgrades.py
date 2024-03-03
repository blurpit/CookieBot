from abc import ABC, abstractmethod
from datetime import datetime

_id_counter = 0

class Upgrade(ABC):
    def __init__(self, name: str):
        self.name = name
        global _id_counter
        self.id = _id_counter
        _id_counter += 1

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

    @abstractmethod
    def get_price(self, level: int) -> int:
        """ Price of the the upgrade at the given level """
        pass

class ClickUpgrade(Upgrade):
    def __init__(self, name, base_cpc: int):
        super().__init__(name)
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
    def __init__(self, name, base_cps: int):
        super().__init__(name)
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
