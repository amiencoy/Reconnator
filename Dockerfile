# ==================================================================================== #
# This is the main Dockerfile for Reconnator's provider-agnostic security agent.       #
# It builds a lightweight Alpine container to run the Telegram bot and the MCP server. #
# CRITICAL: I install docker-cli so this container can spawn our ephemeral tool        #
# containers (Nmap, Ffuf, Nuclei, Subfinder) using the host's Docker daemon (DooD).    #
# NB: main.py is dead. The true entrypoint is now bot.py                               #
# ==================================================================================== #

FROM python:3.14-alpine

LABEL maintainer="amiencoy"
LABEL description="Reconnator - Modern Cloud-Native Recon Bot"

WORKDIR /app

RUN apk upgrade --no-cache \
    && apk add --no-cache docker-cli

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN addgroup -S -g 65532 reconnator \
    && adduser -S -D -H -u 65532 -G reconnator reconnator \
    && mkdir -p /app/generated_reports \
    && chown -R 65532:65532 /app

USER 65532:65532

ENTRYPOINT ["python", "src/bot.py"]
