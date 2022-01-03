# fidelipy

[![docs](https://img.shields.io/readthedocs/qnevx-fidelipy)](https://qnevx-fidelipy.readthedocs.io/)
[![license](https://img.shields.io/github/license/qnevx/fidelipy)](https://www.apache.org/licenses/LICENSE-2.0)
[![pypi](https://img.shields.io/pypi/v/fidelipy)](https://pypi.org/project/fidelipy/)

fidelipy is a simple Python 3.7+ library for semi-automated trading on fidelity.com.
The scope is limited to the `Trade Stocks/ETFs` simplified ticket and
`Trade Mutual Funds` pages.

```python
from fidelipy import Action, Driver, Unit
from selenium.webdriver import Chrome

with Driver(Chrome()) as driver:

    input("Log in, then press enter.")

    try:
        print(driver.cash_available_to_trade("123456789"))

        print(driver.quote("BCDE"))

        driver.market_order("123456789", "BCDE", Action.BUY, Unit.SHARES, "1")

    except Exception:
        print("Report or fix the issue on GitHub.")

    input("Press enter to log out.")
```

> **Warning**
>
> fidelipy asks for manual confirmation: `Place order [Y/n]`
>
> Pressing enter uses the default value Y meaning yes.

## Use

1. [Install a browser driver](https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/).

2. Install fidelipy:

    ```
    pip install fidelipy
    ```

3. Read the [documentation](https://qnevx-fidelipy.readthedocs.io/).

## Build

### Documentation

Install [Sphinx](https://www.sphinx-doc.org/):

```
pip install sphinx
```

Then run this command in the `docs/` directory:

```
make html
```

### Distribution package

Install [build](https://github.com/pypa/build):

```
pip install build
```

Then run this command in the project root directory:

```
python -m build
```
