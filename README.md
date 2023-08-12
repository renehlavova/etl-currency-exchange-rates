# etl-currency-exchange-rates

* **autor:** Renata Hlavova hlavova.renata@gmail.com
* **created:** 2023-08-04

## Description

### What it is used for

ETL module is used for simple extraction, transformation and load of currency exchange rates data from public API.

### What the code does

The `etl-currency-exchange-rates` package does:

1. ECBClient gets currency exchange rates from European Central Bank (ECB).
   - The target currency is EUR by default (based on API settings)
   - The list of base currencies consists of the selected currencies for conversion
   - Dataset is downloaded as JSON on a **daily** basis using the `start_date` while `end_date` is automatically the current day
   - The url is built based on the combination of base and target currency and start/end dates and sends a GET request
   - ECBClient also fills the last known data for missing dates
   - The output is a JSON file consisting of a list of dictionaries with the following keys:
       - `date`
       - `base_currency`
       - `target_currency`
       - `exchange_rate`
2. ECBTransformator transforms the extracted data to the desired format and yields the rows.
   - The inverted conversion is calculated for all the pairs to set EUR as base
   - Dataset is grouped by date, with EUR as base currency and other converted currencies
   - Then, dataset is populated for base currency of selection (i.e. USD)
   - It is possible to reuse the func and set another `from_currency` parameter to change the conversion root
   - The format of outputted rows is the same as in extractor:
        - `date`
        - `base_currency`
        - `target_currency`
        - `exchange_rate`
3. PostgreSQLWriter writes the data to PostgreSQL database.
   - Lists the tables to check whether the table exists: if not, create
   - Creates a temporary table populated with the data from extractor
   - Incrementally loads the data to the destination table
   - Deletes temporary table

## Requirements

See [`pyproject.toml`](./pyproject.toml)

## How to use it

Install this project using `poetry`.

```console
poetry install
```

You need to provide POSTGRES_USER and POSTGRES_PASSWORD and run using:

```console
poe run
```

Or using docker compose:

```console
docker compose run ecb
```

The data are saved in `./postgres-data`. To shutdown PostgreSQL, run:
```console
docker compose down
```

When running using docker compose, the following setup is used:
```console
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_DATABASE=postgres
POSTGRES_PORT=5432
POSTGRES_SCHEMA=public
```

**Optional**:
- TARGET_TABLE: Default value is `currency_exchange_rates`.
- START_DATE: The data will be fetched from this date onwards. Default value is `2023-01-01`.
- BASE_CURRENCIES: Multiple currencies can be provided, separated by commas. Default value is `USD,CZK`.
- TARGET_CURRENCIES: Specifies the target currencies to which the base currencies will be converted. Multiple currencies can be provided, separated by commas. Default value is `CZK,USD,PLN,NOK,RON,ISK,SEK,CHF,TRY,BGN,HUF,DKK,GBP,CAD,AUD`.
