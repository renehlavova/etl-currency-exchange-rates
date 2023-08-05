"""Extracts data about currency exchange rates from European Central Bank API"""

import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin

import backoff
import requests

logger = logging.getLogger(__name__)


class ECBClient:
    """
    Client for European Central Bank API

    https://data.ecb.europa.eu/help/api/data
    """

    def __init__(self):
        self.granularity = "D"
        self.base_currency = "EUR"
        self.session = requests.Session()

        self.base_url = "https://data-api.ecb.europa.eu/service/data/EXR/"
        self.session.params = {
            "endPeriod": datetime.today().strftime("%Y-%m-%d"),
            "detail": "dataonly",
            "includeHistory": "false",
            "format": "jsondata",
        }

    def generate_resource(self, target_currency):
        """
        Generate resource for European Central Bank API
        """

        # As explained in the docs, it is used to uniquely identify exchange rates.
        # - the frequency at which they are measured (e.g. daily - code D);
        # - the currency being measured (e.g. US dollar - code USD);
        # - the currency against which the above currency is being measured (e.g. euro - code EUR);
        # - the type of exchange rates (e.g. foreign exchange reference rates - code SP00);
        # - the Time series variation (e.g. average or standardised measure for a given frequency - code A).

        resource = f"{self.granularity}.{target_currency}.{self.base_currency}.SP00.A"

        return resource

    @backoff.on_exception(backoff.expo, requests.HTTPError, max_tries=5)
    def get_response(self, endpoint, params):
        """Get response from European Central Bank API"""

        logger.info("Requesting %s", endpoint)  # smazat
        response = self.session.get(endpoint, params=params, timeout=60)

        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            if response.status_code == 429 or response.status_code >= 500:
                raise
            raise ValueError(f"Bad response status code - {response.status_code}") from error

        return response.json()

    def clean_response(self, content):
        """Clean response to return dict with dates as keys and rates as values"""

        dates = (date["id"] for date in content["structure"]["dimensions"]["observation"][0]["values"])
        rates = (rate[0] for rate in content["dataSets"][0]["series"]["0:0:0:0:0"]["observations"].values())
        return dict(zip(dates, rates))

    def get_currency_exchange_rate(self, target_currency, start_date):
        """Get currency exchange rates from European Central Bank API as a list of dicts"""

        resource = self.generate_resource(target_currency)
        url = urljoin(self.base_url, resource)

        logger.info("Requesting currency exchange rates from ECB")

        response = self.get_response(url, params={"startPeriod": start_date})
        cln_response = self.clean_response(response)

        return [
            {
                "date": key,
                "base_currency": self.base_currency,
                "target_currency": target_currency,
                "exchange_rate": value,
            }
            for key, value in cln_response.items()
        ]

    def fill_missing_dates(self, data):
        """Fill missing conversions with the last known, typically during weekends and holidays"""

        all_dates = {entry["date"]: entry for entry in data}
        end_date = datetime.today()
        complete_data = []
        current_date = datetime.strptime(min(all_dates), "%Y-%m-%d")
        last_conversion = None

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str in all_dates:
                last_conversion = all_dates[date_str]

            if last_conversion is not None:
                complete_data.append(
                    {
                        "date": date_str,
                        "base_currency": last_conversion["base_currency"],
                        "target_currency": last_conversion["target_currency"],
                        "exchange_rate": last_conversion["exchange_rate"],
                    }
                )

            current_date += timedelta(days=1)

        return complete_data

    def list_currency_exchange_rates(self, target_currency, start_date):
        """Prepare final raw dataset"""

        raw_currency_exchange_rate = self.get_currency_exchange_rate(target_currency, start_date)
        prep_currency_exchange_rate = self.fill_missing_dates(raw_currency_exchange_rate)

        return prep_currency_exchange_rate
