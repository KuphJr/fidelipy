========
Examples
========

Import the required classes:

.. code-block:: python

   from fidelipy import Action, Driver, Unit
   from playwright.sync_api import sync_playwright

Configure web browser
=====================

Create a fidelipy ``Driver`` with a Playwright ``Browser`` instance:

.. code-block:: python

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)

        with Driver(browser) as driver:
            # See examples below.

Playwright supports alternative `Browsers`_ and `settings`_.

.. _`Browsers`: https://playwright.dev/python/docs/browsers
.. _`settings`: https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch

Query basic information
=======================

fidelipy supports querying basic information such as the cash available to trade in an
account and quotes for stocks and ETFs.

.. code-block:: python

    with Driver(browser) as driver:
        input("Log in, then press enter.")

        try:
            print(driver.cash_available_to_trade("123456789"))

            print(driver.quote("BCDE"))

        except Exception:
            print("Report or fix the issue on GitHub.")

        input("Press enter to log out.")

Trade stocks and ETFs
=====================

.. warning::
   fidelipy asks for manual confirmation: ``Place order [Y/n]``

   **Pressing enter uses the default value Y meaning yes.**

fidelipy can help reduce the amount of typing and clicking involved in placing orders.
For stocks and ETFs, it supports market, limit, marketable limit, and good-til-canceled
(GTC) orders.

.. code-block:: python

    with Driver(browser) as driver:
        input("Log in, then press enter.")

        # Buy 1 share of BCDE.
        driver.market_order("123456789", "BCDE", Action.BUY, Unit.SHARES, "1")

        # Sell 100 dollars of BCDE, limit at 50 dollars per share.
        driver.limit_order("123456789", "BCDE", Action.SELL, Unit.DOLLARS, "100", "50")

        # Buy 20.22 dollars of BCDE, limit at ask + 10 cents (default argument).
        driver.marketable_limit_order("123456789", "BCDE", Action.BUY, Unit.DOLLARS, "20.22")

        # Sell 1.234 shares of BCDE, limit at bid - 10 cents (default argument).
        driver.marketable_limit_order("123456789", "BCDE", Action.SELL, Unit.SHARES, "1.234")

        # Buy 1 share of BCDE, limit at 98.76 dollars per share, good-til-canceled.
        driver.gtc_order("123456789", "BCDE", Action.BUY, "1", "98.76")

        input("Press enter to log out.")

Trade mutual funds
==================

.. warning::
   fidelipy asks for manual confirmation: ``Place order [Y/n]``

   **Pressing enter uses the default value Y meaning yes.**

fidelipy supports buy, sell, and exchange orders for mutual funds.

.. code-block:: python

    with Driver(browser) as driver:
        input("Log in, then press enter.")

        # Buy 100 dollars of BCDEX.
        driver.buy_mutual_fund("123456789", "BCDEX", "100")

        # Sell 100 dollars of BCDEX.
        driver.sell_mutual_fund("123456789", "BCDEX", Unit.DOLLARS, "100")

        # Exchange 1 share of BCDEX for CDEFX.
        driver.exchange_mutual_fund("123456789", "BCDEX", Unit.SHARES, "1", "CDEFX")

        input("Press enter to log out.")
