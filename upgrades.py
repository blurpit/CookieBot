from abc import ABC, abstractmethod

from config import SWINDLE_AMOUNT
from util import bignum, percent

_id_counter = 0


class Upgrade(ABC):
    def __init__(self, emoji: str, name: str, hide: bool):
        self.emoji = emoji
        self.name = name
        self.hide = hide
        global _id_counter
        self.id = _id_counter
        _id_counter += 1

    def get_cookies_per_click(self, level: int) -> int:
        """ Cookies per click given by this upgrade at the given level """
        return 0

    def get_cookies_per_second(self, level: int) -> int:
        """ Cookies per second second given by this upgrade at the given level """
        return 0

    def get_swindle_probability(self, level: int) -> float:
        """ Probability of swindling that this upgrade gives at the given level (0.0 to 1.0) """
        return 0

    @abstractmethod
    def get_price(self, level: int) -> int:
        """ Price of the the upgrade at the given level """
        pass

    @abstractmethod
    def get_value_str(self, level: int, hide=False) -> str:
        """ User friendly string representing the value this upgrade provides, eg "+25 / sec" """
        pass

    def get_description(self, level: int) -> str:
        """ User friendly description of the upgrade, shown on the upgrade screen """
        if level == 0:
            return 'Not purchased yet!'
        return f'**{self.get_value_str(level)}**'


class ClickUpgrade(Upgrade):
    def __init__(self, emoji, name, cpc_func, price_func, hide=False):
        super().__init__(emoji, name, hide)
        self.cpc_func = cpc_func
        self.price_func = price_func

    def get_cookies_per_click(self, level):
        if level <= 0:
            return 0
        return self.cpc_func(level)

    def get_price(self, level):
        if level <= 0:
            return 0
        return self.price_func(level)

    def get_value_str(self, level: int, hide=False) -> str:
        if hide and self.hide:
            return '+??? / click'
        cpc = self.get_cookies_per_click(level)
        return f'+{bignum(cpc)} / click'

class PassiveUpgrade(Upgrade):
    def __init__(self, emoji, name, cps_func, price_func, hide=False):
        super().__init__(emoji, name, hide)
        self.cps_func = cps_func
        self.price_func = price_func

    def get_cookies_per_second(self, level):
        if level <= 0:
            return 0
        return self.cps_func(level)

    def get_price(self, level):
        if level <= 0:
            return 0
        return self.price_func(level)

    def get_value_str(self, level: int, hide=False) -> str:
        if hide and self.hide:
            return '+??? / sec'
        cps = self.get_cookies_per_second(level)
        return f'+{bignum(cps)} / sec'


class SwindleUpgrade(Upgrade):
    def __init__(self, emoji, name, prob_func, price_func, hide=False):
        super().__init__(emoji, name, hide)
        self.prob_func = prob_func
        self.price_func = price_func

    def get_swindle_probability(self, level: int):
        if level <= 0:
            return 0
        return self.prob_func(level)

    def get_price(self, level: int) -> int:
        if level <= 0:
            return 0
        return self.price_func(level)

    def get_value_str(self, level: int, hide=False) -> str:
        if level <= 1 and self.hide: # hide only first level
            return '???'
        return percent(self.get_swindle_probability(level))

    def get_description(self, level: int) -> str:
        if level == 0 and self.hide:
            return '???'
        val = self.get_swindle_probability(level)
        return (f"**{percent(val)}** chance to **swindle** {percent(SWINDLE_AMOUNT)} "
                f"of 1st place's cookies when clicking the button")


def print_upgrade_values(upgrades, to_level):
    for u in upgrades:
        print(u.name)
        print('{:<8} {:<25} {}'.format('Lv.', 'Cost', f'🍪'))
        for lvl in range(1, to_level + 1):
            price = u.get_price(lvl)
            if isinstance(u, ClickUpgrade):
                val = bignum(u.get_cookies_per_click(lvl))
            elif isinstance(u, PassiveUpgrade):
                val = bignum((u.get_cookies_per_second(lvl)))
            elif isinstance(u, SwindleUpgrade):
                val = percent(u.get_swindle_probability(lvl))
            else:
                val = '?'
            print('{:<8} {:<25} {}'.format(lvl, bignum(price), val))
        print()
