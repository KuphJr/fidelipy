# Copyright 2022 Darik Harter
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this
# file except in compliance with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

"""Semi-automated trading on fidelity.com.

Must be logged in before calling any driver function.
"""

__all__ = ["Quote", "Action", "Unit", "Driver"]


from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from enum import Enum, auto
from logging import getLogger
from time import sleep
from typing import Any

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import _strings


# dataclass requires Python 3.7+.
@dataclass(frozen=True)
class Quote:
    """Stock or ETF quote.

    Attributes:
        symbol
        name
        last_price
        dollar_change
        percent_change
        bid
        bid_size
        ask
        ask_size
        volume
    """

    symbol: str
    name: str
    last_price: Decimal
    dollar_change: Decimal
    percent_change: Decimal
    bid: Decimal
    bid_size: int
    ask: Decimal
    ask_size: int
    volume: int


class Action(Enum):
    """Action enum for orders.

    Attributes:
        BUY
        SELL
    """

    BUY = auto()
    SELL = auto()


class Unit(Enum):
    """Unit enum for orders.

    Attributes:
        SHARES
        DOLLARS
    """

    SHARES = auto()
    DOLLARS = auto()


def _validate_action(action: Action):
    if action not in (Action.BUY, Action.SELL):
        raise ValueError(_strings.ACTION)


def _validate_unit(unit: Unit):
    if unit not in (Unit.SHARES, Unit.DOLLARS):
        raise ValueError(_strings.UNIT)


def _string(element) -> str:
    return element.get_attribute("innerText").strip()


def _int(string: str) -> int:
    return int(string.replace(",", ""))


def _decimal(string: str) -> Decimal:
    return Decimal(string.translate(str.maketrans("", "", "$,%()")))


def _cents(dollars: str) -> int:
    return int(_decimal(dollars).quantize(Decimal("0.01"), ROUND_DOWN) * 100)


def _dollars(cents: int) -> str:
    return str(Decimal(cents).quantize(Decimal("0.01")) / 100)


def _confirm(prompt: str) -> bool:
    response = input(f"{prompt} [Y/n] ")
    return not response or response.lower() == "y"


class Driver:
    """fidelity.com driver.

    Attributes:
        driver: A Selenium WebDriver instance.
        timeout: The time in seconds to wait for web elements to appear.  Defaults to 10
            seconds.  Must be positive.
        delay: The time in seconds to wait for time-sensitive clicks.  This includes the
            preview order button and mutual fund action dropdown.  Defaults to 1.0
            seconds.  Must be nonnegative.
    """

    def __init__(self, driver: Any, timeout: int = 10, delay: float = 1.0):
        self.__driver = driver
        self.__timeout = timeout
        self.__delay = delay
        self.__logger = getLogger(__name__)

        if self.__timeout <= 0:
            raise ValueError(_strings.DRIVER_TIMEOUT)

        if self.__delay < 0.0:
            raise ValueError(_strings.DRIVER_DELAY)

    def __enter__(self):
        """Get the login page."""
        self.__driver.get(_strings.LOGIN_URL)
        return self

    def __exit__(self, *args):
        """Log out and close the web browser."""
        self.__driver.get(_strings.LOGOUT_URL)
        self.__driver.quit()

    def cash_available_to_trade(self, account: str) -> Decimal:
        """Return the cash available to trade in an account.

        Args:
            account: The Fidelity account number.

        Raises:
            Exception: If the cash available to trade cannot be found.
        """
        try:
            self.__stock_set_account(account)
            return _decimal(_string(self.__by_class_name("funds-cash")))
        except Exception:
            self.__logger.exception("cash available to trade cannot be found")
            raise

    def quote(self, symbol: str) -> Quote:
        """Return the quote for a stock or ETF.

        Args:
            symbol: The stock or ETF symbol.

        Raises:
            Exception: If the quote information cannot be found.
        """
        try:
            self.__driver.get(_strings.TRADE_STOCK_URL)
            self.__stock_set_symbol(symbol)

            name = _string(self.__by_class_name("company-title"))
            last_price = _decimal(_string(self.__by_class_name("last-price")))

            elements = self.__by_class_name(
                "eq-ticket__quote--company-symbol--pricing"
            ).find_elements(By.CLASS_NAME, "eq-ticket__symbol__dollar_percent_chg_font")

            dollar_change = _decimal(_string(elements[0]))
            percent_change = _decimal(_string(elements[1]))

            elements = self.__by_class_name(
                "eq-ticket__quote--blocks-container"
            ).find_elements(By.CLASS_NAME, "block-price-layout")

            parts = _string(elements[0]).split("x")
            bid, bid_size = _decimal(parts[0]), _int(parts[1])
            parts = _string(elements[1]).split("x")
            ask, ask_size = _decimal(parts[0]), _int(parts[1])

            volume = _int(_string(self.__by_class_name("block-volume")))

            return Quote(
                symbol,
                name,
                last_price,
                dollar_change,
                percent_change,
                bid,
                bid_size,
                ask,
                ask_size,
                volume,
            )
        except Exception:
            self.__logger.exception("quote information cannot be found")
            raise

    def download_positions(self) -> None:
        """Download the portfolio positions .csv file.

        Raises:
            Exception: If the positions cannot be downloaded.
        """
        try:
            self.__driver.get(_strings.POSITIONS_URL)
            self.__by_css_selector('button[title="Download"]').click()
        except Exception:
            self.__logger.exception("positions cannot be downloaded")
            raise

    def market_order(
        self, account: str, symbol: str, action: Action, unit: Unit, quantity: str
    ):
        """Place a market order for a stock or ETF.

        Args:
            account: The Fidelity account number.
            symbol: The stock or ETF symbol.
            action: BUY or SELL.
            unit: SHARES or DOLLARS.
            quantity: The amount.

        Returns:
            True if the order is placed successfully, False otherwise.
        """
        _validate_action(action)
        _validate_unit(unit)

        try:
            self.__stock_set_account(account)
            self.__stock_set_symbol(symbol)
            self.__stock_set_action(action)
            self.__stock_set_unit(unit)
            self.__stock_set_quantity(quantity)
            self.__stock_set_market()
            return self.__place_order()
        except Exception:
            self.__logger.exception("market order failed")
            return False

    def limit_order(
        self,
        account: str,
        symbol: str,
        action: Action,
        unit: Unit,
        quantity: str,
        limit: str,
    ):
        """Place a limit order for a stock or ETF.

        Args:
            account: The Fidelity account number.
            symbol: The stock or ETF symbol.
            action: BUY or SELL.
            unit: SHARES or DOLLARS.
            quantity: The amount.
            limit: The limit price in dollars.

        Returns:
            True if the order is placed successfully, False otherwise.
        """
        _validate_action(action)
        _validate_unit(unit)

        try:
            self.__stock_set_account(account)
            self.__stock_set_symbol(symbol)
            self.__stock_set_action(action)
            self.__stock_set_unit(unit)
            self.__stock_set_quantity(quantity)
            self.__stock_set_limit(limit)
            return self.__place_order()
        except Exception:
            self.__logger.exception("limit order failed")
            return False

    def marketable_limit_order(
        self,
        account: str,
        symbol: str,
        action: Action,
        unit: Unit,
        quantity: str,
        buffer: int = 10,
    ):
        """Place a marketable limit order for a stock or ETF.

        Set the limit price at ask + buffer if buying.

        Set the limit price at bid - buffer if selling.

        Args:
            account: The Fidelity account number.
            symbol: The stock or ETF symbol.
            action: BUY or SELL.
            unit: SHARES or DOLLARS.
            quantity: The amount.
            buffer: The limit price buffer in cents.  Defaults to 10.  Must be
                nonnegative.

        Returns:
            True if the order is placed successfully, False otherwise.
        """
        _validate_action(action)
        _validate_unit(unit)
        if buffer < 0:
            raise ValueError(_strings.DRIVER_MARKETABLE_LIMIT_ORDER_BUFFER)

        try:
            self.__stock_set_account(account)
            self.__stock_set_symbol(symbol)
            self.__stock_set_action(action)
            self.__stock_set_unit(unit)
            self.__stock_set_quantity(quantity)

            bid, ask = self.__stock_bid_ask()
            if action == Action.BUY:
                limit = _dollars(ask + buffer)
            elif action == Action.SELL:
                limit = _dollars(bid - buffer)

            self.__stock_set_limit(limit)
            return self.__place_order()
        except Exception:
            self.__logger.exception("marketable limit order failed")
            return False

    def gtc_order(
        self, account: str, symbol: str, action: Action, shares: str, limit: str
    ):
        """Place a good-til-canceled (GTC) order for a stock or ETF.

        Args:
            account: The Fidelity account number.
            symbol: The stock or ETF symbol.
            action: BUY or SELL.
            shares: The number of shares.
            limit: The limit price in dollars.

        Returns:
            True if the order is placed successfully, False otherwise.
        """
        _validate_action(action)

        try:
            self.__stock_set_account(account)
            self.__stock_set_symbol(symbol)
            self.__stock_set_action(action)
            self.__stock_set_unit(Unit.SHARES)
            self.__stock_set_quantity(shares)
            self.__stock_set_limit(limit)
            self.__stock_set_gtc()
            return self.__place_order()
        except Exception:
            self.__logger.exception("good-til-canceled order failed")
            return False

    def buy_mutual_fund(self, account: str, symbol: str, dollars: str):
        """Place a buy order for a mutual fund.

        Args:
            account: The Fidelity account number.
            symbol: The mutual fund symbol.
            dollars: The amount to buy in dollars.

        Returns:
            True if the order is placed successfully, False otherwise.
        """
        try:
            self.__mutual_fund_set_account(account)
            self.__mutual_fund_set_symbol(symbol)
            self.__mutual_fund_set_action(Action.BUY)
            self.__mutual_fund_set_quantity(dollars)
            return self.__place_order()
        except Exception:
            self.__logger.exception("mutual fund buy order failed")
            return False

    def sell_mutual_fund(self, account: str, symbol: str, unit: Unit, quantity: str):
        """Place a sell order for a mutual fund.

        Args:
            account: The Fidelity account number.
            symbol: The mutual fund symbol.
            unit: SHARES or DOLLARS.
            quantity: The amount to sell.

        Returns:
            True if the order is placed successfully, False otherwise.
        """
        _validate_unit(unit)

        try:
            self.__mutual_fund_set_account(account)
            self.__mutual_fund_set_symbol(symbol)
            self.__mutual_fund_set_action(Action.SELL)
            self.__mutual_fund_set_unit(unit)
            self.__mutual_fund_set_quantity(quantity)
            return self.__place_order()
        except Exception:
            self.__logger.exception("mutual fund sell order failed")
            return False

    def exchange_mutual_fund(
        self, account: str, sell_symbol: str, unit: Unit, quantity: str, buy_symbol: str
    ):
        """Place an exchange order for a mutual fund.

        Args:
            account: The Fidelity account number.
            sell_symbol: The symbol of the mutual fund to sell.
            unit: SHARES or DOLLARS.
            quantity: The amount to sell.
            buy_symbol: The symbol of the mutual fund to buy.

        Returns:
            True if the order is placed successfully, False otherwise.
        """
        _validate_unit(unit)

        try:
            self.__mutual_fund_set_account(account)
            self.__mutual_fund_set_symbol(sell_symbol)
            self.__mutual_fund_set_action(None)
            self.__mutual_fund_set_unit(unit)
            self.__mutual_fund_set_quantity(quantity)
            self.__mutual_fund_set_buy_symbol(buy_symbol)
            return self.__place_order()
        except Exception:
            self.__logger.exception("mutual fund exchange order failed")
            return False

    def __stock_set_account(self, account: str):
        self.__driver.get(f"{_strings.TRADE_STOCK_URL}?ACCOUNT={account}")

    def __mutual_fund_set_account(self, account: str):
        self.__driver.get(f"{_strings.TRADE_MUTUAL_FUND_URL}?ACCOUNT={account}")

    def __set_symbol(self, id: str, symbol: str):
        symbol_input = self.__by_id(id)
        symbol_input.clear()
        symbol_input.send_keys(symbol)
        symbol_input.send_keys(Keys.RETURN)

    def __stock_set_symbol(self, symbol: str):
        self.__set_symbol("eq-ticket-dest-symbol", symbol)

    def __mutual_fund_set_symbol(self, symbol: str):
        self.__set_symbol("mf-ticket-dest-symbol-Symbol", symbol)

    def __mutual_fund_set_buy_symbol(self, symbol: str):
        self.__set_symbol("mf-ticket-dest-symbol-Fund to Buy", symbol)

    def __stock_set_action(self, action: Action):
        if action == Action.BUY:
            self.__by_css_selector('label[for="action-buy"]').click()
        elif action == Action.SELL:
            self.__by_css_selector('label[for="action-sell"]').click()

    def __mutual_fund_set_action(self, action: Action):
        self.__by_class_name("mf-ticket__action-dropdown").find_elements(
            By.ID, "mf-dropdownlist-button"
        )[0].click()
        elements = self.__by_class_name("dropdownlist_items").find_elements(
            By.CLASS_NAME, "dropdownlist_items--item"
        )
        sleep(self.__delay)
        for element in elements:
            buy = _string(element) == "Buy" and action == Action.BUY
            sell = _string(element) == "Sell" and action == Action.SELL
            exchange = _string(element) == "Exchange" and action is None
            if buy or sell or exchange:
                element.click()
                break
        sleep(self.__delay)

    def __stock_set_unit(self, unit: Unit):
        if unit == Unit.SHARES:
            self.__by_css_selector('label[for="quantity-type-shares"]').click()
        elif unit == Unit.DOLLARS:
            self.__by_css_selector('label[for="quantity-type-dollars"]').click()

    def __mutual_fund_set_unit(self, unit: Unit):
        if unit == Unit.SHARES:
            self.__by_css_selector('label[for="action-shares"]').click()
        elif unit == Unit.DOLLARS:
            self.__by_css_selector('label[for="action-dollar"]').click()

    def __set_quantity(self, id: str, quantity: str):
        quantity_input = self.__by_id(id)
        quantity_input.clear()
        quantity_input.send_keys(quantity)

    def __stock_set_quantity(self, quantity: str):
        self.__set_quantity("eqt-shared-quantity", quantity)

    def __mutual_fund_set_quantity(self, quantity: str):
        self.__set_quantity("mf-shared-quantity", quantity)

    def __stock_set_market(self):
        self.__by_css_selector('label[for="market-yes"]').click()

    def __stock_set_limit(self, limit: str):
        self.__by_css_selector('label[for="market-no"]').click()
        limit_input = self.__by_id("eqt-ordsel-limit-price-field")
        limit_input.clear()
        limit_input.send_keys(limit)

    def __stock_set_gtc(self):
        self.__by_css_selector('label[for="action-gtc"]').click()

    def __stock_bid_ask(self) -> tuple[int, int]:
        elements = self.__by_class_name(
            "eq-ticket__quote--blocks-container"
        ).find_elements(By.CLASS_NAME, "number")
        bid_ask = tuple(_cents(_string(element)) for element in elements)
        if len(bid_ask) != 2:
            raise RuntimeError("failed to get bid ask")
        return bid_ask

    def __click_preview_order(self):
        sleep(self.__delay)
        self.__by_id("previewOrderBtn").click()

    def __click_place_order(self):
        self.__by_id("placeOrderBtn").click()

    def __place_order(self) -> bool:
        self.__click_preview_order()

        if not _confirm("Place order"):
            return False

        self.__click_place_order()

        return _confirm("Success")

    def __by_class_name(self, class_name: str):
        return WebDriverWait(self.__driver, self.__timeout).until(
            EC.element_to_be_clickable((By.CLASS_NAME, class_name))
        )

    def __by_css_selector(self, css_selector: str):
        return WebDriverWait(self.__driver, self.__timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
        )

    def __by_id(self, id: str):
        return WebDriverWait(self.__driver, self.__timeout).until(
            EC.element_to_be_clickable((By.ID, id))
        )
