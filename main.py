"""Main entrypoint for the etl-currency-exchange-rate package"""

import logging

from etl_currency_exchange_rates.ecb_client import ECBClient
from etl_currency_exchange_rates.ecb_transformator import ECBTransformator

logger = logging.getLogger(__name__)


def main():
    """Main entrypoint"""

    # CONFIGURATION STEP

    start_date = "2023-08-04"

    base_currency = "USD"

    target_currencies = [
        "CZK",
        "USD",
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
        "CAD",
        "AUD",
    ]

    # EXTRACTION STEP

    client = ECBClient()

    raw_data = []

    for target_currency in target_currencies:
        raw_currency_exchange_rate = client.list_currency_exchange_rates(target_currency, start_date)
        raw_data.extend(raw_currency_exchange_rate)

    # TRANSFORMATION STEP

    transformator = ECBTransformator(raw_data)
    transformator.calculate_base_currency(base_currency)
    transformator.calculate_base_currency("CZK", from_currency="USD")

    for line in transformator:
        print(line)


if __name__ == "__main__":
    main()
