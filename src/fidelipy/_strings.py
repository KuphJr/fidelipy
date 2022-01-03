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

"""fidelipy strings."""

# URLs
LOGIN_URL = "https://digital.fidelity.com/prgw/digital/login/full-page"
LOGOUT_URL = "https://login.fidelity.com/ftgw/Fidelity/RtlCust/Logout/Init?AuthRedUrl=https://www.fidelity.com/customer-service/customer-logout"
POSITIONS_URL = "https://oltx.fidelity.com/ftgw/fbc/oftop/portfolio#positions"
TRADE_STOCK_URL = "https://digital.fidelity.com/ftgw/digital/trade-equity/index"
TRADE_MUTUAL_FUND_URL = "https://digital.fidelity.com/ftgw/digital/trade-mutualfund"

# Action
ACTION = "action must be Action.BUY or Action.SELL"

# Unit
UNIT = "unit must be Unit.SHARES or Unit.DOLLARS"

# Driver
DRIVER_TIMEOUT = "timeout must be positive"
DRIVER_DELAY = "delay must be nonnegative"
DRIVER_MARKETABLE_LIMIT_ORDER_BUFFER = "buffer must be nonnegative"
