# etl-currency-exchange-rates

* **autor:** Renata Hlavova hlavova.renata@gmail.com
* **created:** 2023-08-04

## Description

This package prepares a currency exchange rates table. Since there are multiple sources for data, my reasoning was as following:

- I was primarily inclined to look for the primary source, i.e. ECB Bank 
- I also checked third-party APIs such as Fixer API or Exchange Rates API which provided the data in the desired structure (and as a reference, KBC uses Fixer for their component which was a good starting point to check), but I decided not to use them due to limitations in their free versions
    - limited number of API calls
    - supported only http
    - not possible to change base currency
- I was also searching for US sources as based on the assignment, the USD currency seems to be the reference currency
    - I eventually decided to use the ECB and two-way conversion (USD -> EUR -> target currency)

I chose ETL over ELT approach because:

- The historical currency exchange rates remain unchanged, with updates only affecting the latest day's rates. Since the transformation requirements are consistent across historical data, it makes sense to perform the necessary transformations during the extraction phase itself, allowing the data to be directly prepared in the desired structure before loading.
- The amount of currency exchange rate data is not substantial, and we can predict the data volume. Given the manageable size of the dataset, the transformation process can be efficiently handled during the extraction stage without the need for an additional transformation layer in the database.

By leveraging the ETL approach under these circumstances, we can avoid unnecessary complexities associated with ELT. 

The selection of solution and approach:

- The solution is broken down into three components (ECBClient, ECBTransformator, and PostgreSQLWriter), each responsible for specific tasks: easy maintenance, debugging, and future enhancements
- The solution fetches data directly from the European Central Bank (ECB), ensuring accurate and reliable up-to-date currency exchange rates
- The solution allows users to select various base currencies for conversion, making it adaptable to different currency conversion requirements

Communication, what value the final data could have:

- The data is valuable for financial reporting, budgeting, and forecasting, i.e. for businesses operating in multiple countries + market insights and other analyses related to currencies
- I would highlight the reliability of the source data and automated daily extracts with latest up-to-date rates, consistent and easy format ready for further analysis

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

### Installation

Install this project using `poetry`.

```console
poetry install
```

### Other commands

* `poe isort`
  * sort imports using `isort`
* `poe isort-check`
  * check imports are sorted using `isort`
* `poe black`
  * format Python files using `black`
* `poe black-check`
  * check Python formatting using `black`
* `poe pylint`
  * use `pylint` to lint your Python files
* `poe format`
  * run `isort` and `black` in succession
* `poe lint`
  * run `isort-check`, `black-check`, `pylint` in succession