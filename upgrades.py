from abc import ABC, abstractmethod
from datetime import datetime

_id_counter = 0

class Upgrade(ABC):
    def __init__(self, name: str, emoji: str, unit: str):
        self.name = name
        self.emoji = emoji
        self.unit = unit
        global _id_counter
        self.id = _id_counter
        _id_counter += 1

    @abstractmethod
    def get_cookies_since(self, timestamp: datetime, level: int) -> int:
        """ How many cookies given between `timestamp` and now, rounding DOWN
            to the nearest second """
        pass

    @abstractmethod
    def get_cookies_per_unit(self, level: int) -> int:
        """ Cookies per unit (click or second) given by this upgrade at the given level """
        pass

    @abstractmethod
    def get_price(self, level: int) -> int:
        """ Price of the the upgrade at the given level """
        pass

class ClickUpgrade(Upgrade):
    def __init__(self, name, base_cpc: int):
        super().__init__(name, '👆', 'click')
        self.base_cpc = base_cpc

    def get_cookies_since(self, timestamp, level):
        return 0

    def get_cookies_per_unit(self, level):
        if level == 0:
            return 0
        return self.base_cpc * 2**(level - 1)

    def get_price(self, level):
        # if level == 0:
        #     return 0
        # return 100 * 2**(level - 1)
        return 1

class PassiveUpgrade(Upgrade):
    def __init__(self, name, base_cps: int):
        super().__init__(name, '🕙', 'sec')
        self.base_cps = base_cps

    def get_cookies_since(self, timestamp, level):
        if self.base_cps == 0:
            return 0
        now = datetime.utcnow()
        delta = int((now - timestamp).total_seconds())
        return max(delta * self.get_cookies_per_unit(level), 0)

    def get_cookies_per_unit(self, level):
        if level == 0:
            return 0
        return self.base_cps * 2**(level - 1)

    def get_price(self, level):
        # if level == 0:
        #     return 0
        # return 100 * 2**(level - 1)
        return 1
