"""Main entrypoint for the etl-currency-exchange-rate package"""

import logging
import os
from dotenv import load_dotenv

from etl_currency_exchange_rates.ecb_client import ECBClient
from etl_currency_exchange_rates.ecb_transformator import ECBTransformator
from etl_currency_exchange_rates.postgres_writer import PostgreSQLWriter

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


def main():
    """Main entrypoint"""

    load_dotenv()

    target_table = os.getenv("TARGET_TABLE", "currency_exchange_rates")
    start_date = os.getenv("START_DATE", "2023-01-01")
    base_currencies = os.getenv("BASE_CURRENCIES", "USD,CZK").split(",")
    target_currencies = os.getenv(
        "TARGET_CURRENCIES", "CZK,USD,PLN,NOK,RON,ISK,SEK,CHF,TRY,BGN,HUF,DKK,GBP,CAD,AUD"
    ).split(",")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_database = os.getenv("POSTGRES_DATABASE", "postgres")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_schema = os.getenv("POSTGRES_SCHEMA", "public")
    postgres_user = os.environ["POSTGRES_USER"]
    postgres_password = os.environ["POSTGRES_PASSWORD"]

    client = ECBClient()

    raw_data = []

    logger.info("Requesting currency exchange rates from ECB")

    for target_currency in target_currencies:
        raw_currency_exchange_rate = client.list_currency_exchange_rates(target_currency, start_date)
        raw_data.extend(raw_currency_exchange_rate)

    logger.info("Transforming currency exchange rates")

    transformator = ECBTransformator(raw_data)

    for base_currency in base_currencies:
        transformator.calculate_base_currency(base_currency)
        # possible to calculate from other base currency
        # transformator.calculate_base_currency(base_currency, from_currency="USD")

    logger.info("Writing currency exchange rates to PostgreSQL")

    writer = PostgreSQLWriter(
        database=postgres_database,
        user=postgres_user,
        password=postgres_password,
        host=postgres_host,
        port=postgres_port,
        schema=postgres_schema,
    )

    with writer:
        writer.upsert_exchange_rate_data(target_table, transformator)


if __name__ == "__main__":
    main()
