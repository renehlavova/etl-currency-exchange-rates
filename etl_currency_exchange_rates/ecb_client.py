"""Extracts data about currency exchange rates from European Central Bank API"""

import logging
from datetime import datetime
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
        self.target_currency = "EUR"
        self.session = requests.Session()

        self.base_url = "https://data-api.ecb.europa.eu/service/data/EXR/"
        self.session.params = {
            "endPeriod": datetime.today().strftime("%Y-%m-%d"),
            "detail": "dataonly",
            "includeHistory": "false",
            "format": "jsondata",
        }

    def generate_resource(self, base_currency):
        """
        Generate resource for European Central Bank API
        """

        # As explained in the docs, it is used to uniquely identify exchange rates.
        # - the frequency at which they are measured (e.g. daily - code D);
        # - the currency being measured (e.g. US dollar - code USD);
        # - the currency against which the above currency is being measured (e.g. euro - code EUR);
        # - the type of exchange rates (e.g. foreign exchange reference rates - code SP00);
        # - the Time series variation (e.g. average or standardised measure for a given frequency - code A).

        resource = f"{self.granularity}.{base_currency}.{self.target_currency}.SP00.A"

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

    def get_currency_exchange_rate(self, base_currency, start_date):
        """Get base currency exchange rates from European Central Bank API"""

        resource = self.generate_resource(base_currency)
        url = urljoin(self.base_url, resource)

        logger.info("Requesting currency exchange rates from ECB")

        response = self.get_response(url, params={"startPeriod": start_date})
        cln_response = self.clean_response(response)

        return [
            {
                "date": key,
                "base_currency": base_currency,
                "target_currency": self.target_currency,
                "exchange_rate": value,
            }
            for key, value in cln_response.items()
        ]
