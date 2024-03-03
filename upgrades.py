from abc import ABC, abstractmethod
from datetime import datetime

class Upgrade(ABC):
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    @abstractmethod
    def get_cookies_since(self, timestamp: datetime, n: int) -> int:
        """ How many cookies given between `timestamp` and now, rounding DOWN
            to the nearest second """
        pass

    @abstractmethod
    def get_cookies_per_second(self, n: int) -> int:
        """ Cookies per second given by the `n`th copy of this upgrade """
        pass

    @abstractmethod
    def get_cookies_per_click(self, n: int) -> int:
        """ Cookies per click given by `n`th copy of this upgrade """
        pass

    @abstractmethod
    def get_description(self, n: int) -> str:
        pass

class ClickUpgrade(Upgrade):
    def __init__(self, id, name, base_cpc: int):
        super().__init__(id, '👆 ' + name)
        self.base_cpc = base_cpc

    def get_cookies_since(self, timestamp, n):
        return 0

    def get_cookies_per_second(self, n):
        return 0

    def get_cookies_per_click(self, n):
        return self.base_cpc * n

    def get_description(self, n):
        return f'🍪 +{self.get_cookies_per_click(n)} / click'

class PassiveUpgrade(Upgrade):
    def __init__(self, id: int, name, base_cps: int):
        super().__init__(id, '🕙 ' + name)
        self.base_cps = base_cps

    def get_cookies_since(self, timestamp, n):
        if self.base_cps == 0:
            return 0
        now = datetime.utcnow()
        delta = int((now - timestamp).total_seconds())
        return max(delta * self.get_cookies_per_second(n), 0)

    def get_cookies_per_second(self, n):
        return self.base_cps * n

    def get_cookies_per_click(self, n):
        return 0

    def get_description(self, n):
        return f'🍪 +{self.get_cookies_per_second(n)} / sec'
