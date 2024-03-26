from abc import ABC, abstractmethod
from datetime import datetime

_id_counter = 0


class Upgrade(ABC):
    def __init__(self, emoji: str, name: str, unit: str, hide=False):
        self.emoji = emoji
        self.name = name
        self.unit = unit
        self.hide = hide
        global _id_counter
        self.id = _id_counter
        _id_counter += 1

    @abstractmethod
    def get_cookies_per_unit(self, level: int) -> int:
        """ Cookies per unit (click or second) given by this upgrade at the given level """
        pass

    @abstractmethod
    def get_price(self, level: int) -> int:
        """ Price of the the upgrade at the given level """
        pass

class ClickUpgrade(Upgrade):
    def __init__(self, emoji, name, cpc_func, price_func, hide=False):
        super().__init__(emoji, name, 'click', hide=hide)
        self.cpc_func = cpc_func
        self.price_func = price_func

    def get_cookies_per_unit(self, level):
        if level <= 0:
            return 0
        return self.cpc_func(level)

    def get_price(self, level):
        if level <= 0:
            return 0
        return self.price_func(level)

class PassiveUpgrade(Upgrade):
    def __init__(self, emoji, name, cps_func, price_func, hide=False):
        super().__init__(emoji, name, 'sec', hide)
        self.cps_func = cps_func
        self.price_func = price_func

    def get_cookies_per_unit(self, level):
        if level <= 0:
            return 0
        return self.cps_func(level)

    def get_price(self, level):
        if level <= 0:
            return 0
        return self.price_func(level)
