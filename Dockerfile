FROM python:3.11-slim

ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="${PATH}:/root/.local/bin"

RUN apt-get update && apt-get install -y curl postgresql-common build-essential libpq-dev

RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install

ADD . .

CMD ["poe", "run"]