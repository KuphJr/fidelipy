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
from pathlib import Path

from playwright.sync_api import Browser

from . import _strings


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


def _validate_action(action: Action) -> None:
    if action not in (Action.BUY, Action.SELL):
        raise ValueError(_strings.ACTION)


def _validate_unit(unit: Unit) -> None:
    if unit not in (Unit.SHARES, Unit.DOLLARS):
        raise ValueError(_strings.UNIT)


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
        browser: The Playwright Browser_ to use.
        timeout: The time in seconds to wait for web elements to appear.  Defaults to 10
            seconds.  Must be positive.

    .. _browser: https://playwright.dev/python/docs/api/class-browser
    """

    def __init__(self, browser: Browser, timeout: int = 10):
        self.__browser = browser
        self.__logger = getLogger(__name__)

        if timeout <= 0:
            raise ValueError(_strings.DRIVER_TIMEOUT)

        self.__page = self.__browser.new_page()
        self.__page.set_default_timeout(timeout * 1000)

    def __enter__(self):
        """Navigate to the login page."""
        self.__page.goto(_strings.LOGIN_URL)
        return self

    def __exit__(self, *args) -> None:
        """Log out and close the web browser."""
        self.__page.goto(_strings.LOGOUT_URL)
        self.__browser.close()

    def cash_available_to_trade(self, account: str) -> Decimal:
        """Return the cash available to trade in an account.

        Args:
            account: The Fidelity account number.

        Raises:
            Exception: If the cash available to trade cannot be found.
        """
        try:
            self.__stock_set_account(account)
            return _decimal(self.__inner_text(".funds-cash"))
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
            self.__page.goto(_strings.TRADE_STOCK_URL)
            self.__stock_set_symbol(symbol)

            name = self.__inner_text(".company-title")
            last_price = _decimal(self.__inner_text(".last-price"))

            changes = self.__inner_texts(".eq-ticket__symbol__dollar_percent_chg_font")
            dollar_change = _decimal(changes[0])
            percent_change = _decimal(changes[1])

            elements = self.__inner_texts(".block-price-layout")
            parts = elements[0].split("x")
            bid, bid_size = _decimal(parts[0]), _int(parts[1])
            parts = elements[1].split("x")
            ask, ask_size = _decimal(parts[0]), _int(parts[1])

            volume = _int(self.__inner_text(".block-volume"))

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

    def download_positions(self) -> Path:
        """Download the portfolio positions .csv file.

        Returns:
            The path to a temporary file.

        Raises:
            Exception: If the file cannot be downloaded.
        """
        try:
            self.__page.goto(_strings.POSITIONS_URL)
            with self.__page.expect_download() as info:
                self.__page.click("button[title='Download']")
            path = info.value.path()
            if not path:
                raise Exception
            return path
        except Exception:
            self.__logger.exception("file cannot be downloaded")
            raise

    def market_order(
        self, account: str, symbol: str, action: Action, unit: Unit, quantity: str
    ) -> bool:
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
    ) -> bool:
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
    ) -> bool:
        """Place a marketable limit order for a stock or ETF.

        Set the limit price at ask + buffer if buying.

        Set the limit price at bid - buffer if selling.

        Args:
            account: The Fidelity account number.
            symbol: The stock or ETF symbol.
            action: BUY or SELL.
            unit: SHARES or DOLLARS.
            quantity: The amount.
            buffer: The limit price buffer in cents.  Defaults to 10 cents.  Must be
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
    ) -> bool:
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

    def buy_mutual_fund(self, account: str, symbol: str, dollars: str) -> bool:
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
            self.__mutual_fund_wait_for_symbol()
            self.__mutual_fund_set_action("Buy")
            self.__mutual_fund_set_quantity(dollars)
            return self.__place_order()
        except Exception:
            self.__logger.exception("mutual fund buy order failed")
            return False

    def sell_mutual_fund(
        self, account: str, symbol: str, unit: Unit, quantity: str
    ) -> bool:
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
            self.__mutual_fund_wait_for_symbol()
            self.__mutual_fund_set_action("Sell")
            self.__mutual_fund_set_unit(unit)
            self.__mutual_fund_set_quantity(quantity)
            return self.__place_order()
        except Exception:
            self.__logger.exception("mutual fund sell order failed")
            return False

    def exchange_mutual_fund(
        self, account: str, sell_symbol: str, unit: Unit, quantity: str, buy_symbol: str
    ) -> bool:
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
            self.__mutual_fund_wait_for_symbol()
            self.__mutual_fund_set_action("Exchange")
            self.__mutual_fund_set_unit(unit)
            self.__mutual_fund_set_quantity(quantity)
            self.__mutual_fund_set_buy_symbol(buy_symbol)
            self.__mutual_fund_wait_for_buy_symbol()
            return self.__place_order()
        except Exception:
            self.__logger.exception("mutual fund exchange order failed")
            return False

    def __inner_text(self, selector: str) -> str:
        return self.__page.inner_text(selector).strip()

    # Type hint requires Python 3.9+.
    def __inner_texts(self, selector: str) -> list[str]:
        return [
            text.strip() for text in self.__page.locator(selector).all_inner_texts()
        ]

    def __stock_set_account(self, account: str) -> None:
        self.__page.goto(f"{_strings.TRADE_STOCK_URL}?ACCOUNT={account}")

    def __mutual_fund_set_account(self, account: str) -> None:
        self.__page.goto(f"{_strings.TRADE_MUTUAL_FUND_URL}?ACCOUNT={account}")

    def __set_symbol(self, selector: str, symbol: str) -> None:
        symbol_input = self.__page.locator(selector)
        symbol_input.fill(symbol)
        symbol_input.press("Enter")

    def __stock_set_symbol(self, symbol: str) -> None:
        self.__set_symbol("text=Symbol", symbol)

    def __mutual_fund_set_symbol(self, symbol: str) -> None:
        self.__stock_set_symbol(symbol)

    def __mutual_fund_set_buy_symbol(self, symbol: str) -> None:
        self.__set_symbol("text=Fund to Buy", symbol)

    def __mutual_fund_wait_for_symbol(self) -> None:
        self.__page.locator(".detail-value").wait_for()

    def __mutual_fund_wait_for_buy_symbol(self) -> None:
        self.__page.locator("#mf-ticket__second-quote-box .detail-value").wait_for()

    def __stock_set_action(self, action: Action) -> None:
        if action == Action.BUY:
            self.__page.click("text=Buy")
        elif action == Action.SELL:
            self.__page.click("text=Sell")

    def __mutual_fund_set_action(self, action: str) -> None:
        self.__page.click("text=Action")
        self.__page.click(f"text={action}")

    def __stock_set_unit(self, unit: Unit) -> None:
        if unit == Unit.SHARES:
            self.__page.click("label:has-text('Shares')")
        elif unit == Unit.DOLLARS:
            self.__page.click("text=Dollars")

    def __mutual_fund_set_unit(self, unit: Unit) -> None:
        self.__stock_set_unit(unit)

    def __stock_set_quantity(self, quantity: str) -> None:
        self.__page.fill("#eqt-shared-quantity", quantity)

    def __mutual_fund_set_quantity(self, quantity: str) -> None:
        self.__page.fill("#mf-shared-quantity", quantity)

    def __stock_set_market(self) -> None:
        self.__page.click("label:has-text('Market')")

    def __stock_set_limit(self, limit: str) -> None:
        self.__page.click("text=Limit")
        self.__page.fill("text=Limit Price", limit)

    def __stock_set_gtc(self) -> None:
        self.__page.click("text=GTC")

    def __stock_bid_ask(self) -> tuple[int, ...]:
        bid_ask = tuple(_cents(number) for number in self.__inner_texts(".number"))
        if len(bid_ask) != 2:
            raise RuntimeError("failed to get bid ask")
        return bid_ask

    def __click_preview_order(self) -> None:
        self.__page.click("#previewOrderBtn")

    def __click_place_order(self) -> None:
        self.__page.click("#placeOrderBtn")

    def __place_order(self) -> bool:
        self.__click_preview_order()

        if not _confirm("Place order"):
            return False

        self.__click_place_order()

        return _confirm("Success")
