"""Writer class for PostgreSQL database."""

from contextlib import contextmanager
import logging
from uuid import uuid4
import psycopg2

logger = logging.getLogger(__name__)


class PostgreSQLWriter:
    """Writer class for PostgreSQL database."""

    def __init__(self, database, user, password, host, port, schema="public"):
        self.database = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.schema = schema
        self.connection = None

    def __enter__(self):
        self.connection = self.connect()
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.close()

    def connect(self):
        """Connect to PostgreSQL database"""

        try:
            self.connection = psycopg2.connect(
                dbname=self.database, user=self.user, password=self.password, host=self.host, port=self.port
            )
            self.connection.autocommit = True
            logger.info("Connected to %s, %s as %s", self.database, self.host, self.user)
        except psycopg2.Error as error:
            logger.error("Error connecting to PostgreSQL: %s", error)
            raise

        return self.connection

    def close(self):
        """Close connection to PostgreSQL database"""

        if self.connection:
            self.connection.close()
            logger.info("Connection to PostgreSQL closed.")

    @contextmanager
    def provide_cursor(self):
        """Provide cursor for PostgreSQL database"""

        assert self.connection, "Connection to PostgreSQL is not established."
        cursor = self.connection.cursor()
        yield cursor
        cursor.close()

    def list_tables(self):
        """List all tables in PostgreSQL database"""

        with self.provide_cursor() as cur:
            cur.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s;
                """,
                (self.schema,),
            )

            return [row[0] for row in cur.fetchall()]

    def create_table(self, table_name):
        """Create table in PostgreSQL database"""

        with self.provide_cursor() as cur:
            if table_name in self.list_tables():
                logger.warning("Table %s already exists.", table_name)
                return

            cur.execute(
                f"""
                CREATE TABLE "{self.schema}"."{table_name}" (
                    date DATE,
                    from_currency VARCHAR, 
                    to_currency VARCHAR, 
                    exchange_rate FLOAT,
                    primary key (date, from_currency, to_currency)
                )
                """
            )

        logger.info("Table %s created.", table_name)

    def upsert_data(self, source_table, target_table):
        """Upsert data into PostgreSQL database"""

        with self.provide_cursor() as cur:
            cur.execute(
                f"""
                MERGE INTO "{self.schema}"."{target_table}" AS target
                USING "{self.schema}"."{source_table}" AS source 
                
                ON source.date = target.date 
                    AND source.from_currency = target.from_currency 
                    AND source.to_currency = target.to_currency
                
                WHEN NOT MATCHED THEN
                INSERT (date, from_currency, to_currency, exchange_rate)
                VALUES (source.date, source.from_currency, source.to_currency, source.exchange_rate)
                
                WHEN MATCHED THEN
                UPDATE 
                SET exchange_rate = source.exchange_rate
                """
            )

        logger.info("Data upserted from %s to %s.", source_table, target_table)

    def insert_data(self, table_name, data):
        """Insert data into PostgreSQL database"""

        with self.provide_cursor() as cur:
            cur.executemany(
                f"""
                INSERT INTO "{self.schema}"."{table_name}" (date, from_currency, to_currency, exchange_rate)
                VALUES (%s, %s, %s, %s)
                """,
                [(row["date"], row["base_currency"], row["target_currency"], row["exchange_rate"]) for row in data],
            )

        logger.info("Data inserted into %s.", table_name)

    def delete_table(self, table_name):
        """Delete table in PostgreSQL database"""

        with self.provide_cursor() as cur:
            cur.execute(
                f"""
                DROP TABLE "{self.schema}"."{table_name}"
                """,
            )

        logger.info("Table %s deleted.", table_name)

    def upsert_exchange_rate_data(self, table_name, data):
        """Upsert exchange rate data into PostgreSQL database"""

        self.create_table(table_name)
        tmp_name = f"tmp_{uuid4().hex}"
        self.create_table(tmp_name)
        self.insert_data(tmp_name, data)
        self.upsert_data(tmp_name, table_name)
        self.delete_table(tmp_name)
