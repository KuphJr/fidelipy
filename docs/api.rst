===
API
===

.. automodule:: fidelipy

.. autoclass:: fidelipy.Quote

.. autoclass:: fidelipy.Action

.. autoclass:: fidelipy.Unit

.. autoclass:: fidelipy.Driver

Query basic information
=======================

   .. automethod:: fidelipy.Driver.cash_available_to_trade

   .. automethod:: fidelipy.Driver.quote

   .. automethod:: fidelipy.Driver.download_positions

Trade stocks and ETFs
=====================

   .. warning::
      fidelipy asks for manual confirmation: ``Place order [Y/n]``

      **Pressing enter uses the default value Y meaning yes.**

   .. automethod:: fidelipy.Driver.market_order

   .. automethod:: fidelipy.Driver.limit_order

   .. automethod:: fidelipy.Driver.marketable_limit_order

   .. automethod:: fidelipy.Driver.gtc_order

Trade mutual funds
==================

   .. warning::
      fidelipy asks for manual confirmation: ``Place order [Y/n]``

      **Pressing enter uses the default value Y meaning yes.**

   .. automethod:: fidelipy.Driver.buy_mutual_fund

   .. automethod:: fidelipy.Driver.sell_mutual_fund

   .. automethod:: fidelipy.Driver.exchange_mutual_fund
