"""Transformation step of ECB currency exchange rates data"""

import logging

logger = logging.getLogger(__name__)


class ECBTransformator:
    """Transformator class for ECB currency exchange rates data"""

    def __init__(self, data):
        inverted_data = self._from_eur_to_currency(data)
        self._data = {"EUR": self._group_currencies_by_date(inverted_data)}

    def _from_eur_to_currency(self, data):
        """Convert all exchange rates to EUR as base currency"""

        updated_data = []

        for entry in data:
            if entry["base_currency"] == "EUR":
                updated_data.append(entry)

                new_entry = entry.copy()
                new_entry["target_currency"] = entry["base_currency"]
                new_entry["base_currency"] = entry["target_currency"]
                new_entry["exchange_rate"] = 1 / entry["exchange_rate"]
                updated_data.append(new_entry)

        return updated_data

    def _group_currencies_by_date(self, data):
        """Transform all currencies to one dict per date"""
        result = {}

        for entry in data:
            if entry["target_currency"] == "EUR":
                continue

            date = entry["date"]
            target_currency = entry["target_currency"]
            exchange_rate = entry["exchange_rate"]

            result.setdefault(date, {"EUR": 1.0})

            result[date][target_currency] = exchange_rate

        return result

    def _set_base_currency(self, data, base_currency):
        """
        Get daily exchange rates with selected base currency and EUR as target currency
        to be used for conversion to other currencies
        """

        return {date: rates[base_currency] for date, rates in data.items()}

    def calculate_base_currency(self, base_currency, from_currency="EUR"):
        """
        Convert all exchange rates to selected currency using following formula.

        USD selected as base currency = (USD to EUR) * (EUR to CZK)
        or similarly = (1 / EUR to USD) * (EUR to CZK)
        """

        if base_currency in self._data:
            return

        if base_currency == from_currency:
            raise ValueError("Base currency cannot be the same as from currency")

        conversion_dict = self._set_base_currency(self._data[from_currency], base_currency)

        base_data = {}

        for date, currency_rates in self._data[from_currency].items():
            base_data[date] = {base_currency: 1.0}

            for currency, currency_rate in currency_rates.items():
                if currency != base_currency:
                    base_data[date][currency] = (1 / conversion_dict[date]) * currency_rate

        self._data[base_currency] = base_data

    def iter_rows(self):
        """Iterate over all rows in the dataset"""

        for base_currency, data in self._data.items():
            for date, currency_rates in data.items():
                for currency, currency_rate in currency_rates.items():
                    yield {
                        "date": date,
                        "base_currency": base_currency,
                        "target_currency": currency,
                        "exchange_rate": currency_rate,
                    }

    def __iter__(self):
        return self.iter_rows()
