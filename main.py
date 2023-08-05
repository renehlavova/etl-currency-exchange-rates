"""Main entrypoint for the etl-currency-exchange-rate package"""

import logging

from etl_currency_exchange_rates.ecb_client import ECBClient

logger = logging.getLogger(__name__)


def main():
    """Main entrypoint"""

    client = ECBClient()
    base_currencies = [
        "PLN",
        "NOK",
        "RON",
        "ISK",
        "SEK",
        "CHF",
        "CZK",
        "TRY",
        "BGN",
        "HUF",
        "DKK",
        "GBP",
        "USD",
        "CAD",
        "AUD",
    ]

    for base_currency in base_currencies:
        print(client.get_currency_exchange_rate(base_currency, start_date="2023-07-21"))


if __name__ == "__main__":
    main()
