ARG NAUTOBOT_VER="1.3.5"
ARG PYTHON_VER=3.8
FROM ghcr.io/nautobot/nautobot-dev:${NAUTOBOT_VER}-py${PYTHON_VER}

ARG NAUTOBOT_VER=${NAUTOBOT_VER}

ENV prometheus_multiproc_dir=/prom_cache

ARG NAUTOBOT_ROOT=/opt/nautobot

ENV NAUTOBOT_ROOT ${NAUTOBOT_ROOT}

RUN apt-get update && apt-get install -y gcc libmariadb-dev-compat libmariadb-dev libgeos-dev

WORKDIR $NAUTOBOT_ROOT

# Configure poetry
RUN poetry config virtualenvs.create false \
    && poetry config installer.parallel false

# -------------------------------------------------------------------------------------
# Install Nautobot Plugin
# -------------------------------------------------------------------------------------

WORKDIR /source

# Copy in only pyproject.toml/poetry.lock to help with caching this layer if no updates to dependencies
COPY poetry.lock pyproject.toml /source/

# Add Nautobot to the poetry file for testing
RUN poetry add nautobot==$NAUTOBOT_VER

# --no-root declares not to install the project package since we're wanting to take advantage of caching dependency installation
# and the project is copied in and installed after this step
RUN poetry install --no-interaction --no-ansi --no-root -E metrics

# Copy in the rest of the source code and install local Nautobot plugin
COPY . /source
RUN poetry install --no-interaction --no-ansi -E metrics

COPY development/nautobot_config.py /opt/nautobot/nautobot_config.py
