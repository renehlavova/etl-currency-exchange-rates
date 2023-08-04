"""Extracts data about currency exchange rates from Fixer API"""

import logging
from urllib.parse import urljoin

import backoff
import requests

logger = logging.getLogger(__name__)


class FixerClient:
    """
    Client for Fixer API

    https://fixer.io/documentation
    """

    def __init__(self, api_key, base_currency, target_currencies):
        self.access_key = api_key
        self.base_currency = base_currency
        self.target_currencies = target_currencies
        self.session = requests.Session()

        self.base_url = "http://data.fixer.io/api"
        self.params = {
            "access_key": self.access_key,
            "base": self.base_currency,
            "symbols": self.target_currencies,
        }

    @backoff.on_exception(backoff.expo, requests.HTTPError, max_tries=5)
    def get_response(self, endpoint):
        """Get response from Fixer API"""

        logger.info("Requesting %s", endpoint)
        response = self.session.get(endpoint, params=self.params, timeout=15)

        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            if response.status_code == 429 or response.status_code >= 500:
                raise
            raise ValueError(f"Bad response status code - {response.status_code}") from error

        if not response.json()["success"]:
            raise ValueError(response.json()["error"]["type"]) from None

        return response.json()

    def get_latest_rates(self):
        """Get the latest currency exchange rates from Fixer API"""

        endpoint = urljoin(self.base_url, "latest")
        response = self.get_response(endpoint)
        return response

    def get_historical_rates(self, date):
        """Get historical currency exchange rates from Fixer API"""

        endpoint = urljoin(self.base_url, date)
        response = self.get_response(endpoint)
        return response
