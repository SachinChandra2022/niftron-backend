FROM python:3.11-slim-bookworm

ARG AIRFLOW_VERSION=2.9.2
ARG PYTHON_VERSION=3.11
ARG CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW_UID=50000

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        curl \
        gcc \
        python3-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements-airflow.txt /requirements.txt

RUN curl -sSLo /constraints.txt "${CONSTRAINT_URL}" && \
    pip install --no-cache-dir -r /requirements.txt -c /constraints.txt

RUN useradd -ms /bin/bash -u ${AIRFLOW_UID} airflow && \
    mkdir -p ${AIRFLOW_HOME}/dags ${AIRFLOW_HOME}/logs ${AIRFLOW_HOME}/plugins && \
    chown -R airflow:airflow ${AIRFLOW_HOME}

USER airflow
WORKDIR ${AIRFLOW_HOME}