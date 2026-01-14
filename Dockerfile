FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN adduser agentbeats
USER agentbeats
WORKDIR /home/agentbeats

COPY pyproject.toml uv.lock README.md ./
COPY src src
COPY problems problems

RUN \
    --mount=type=cache,target=/home/agentbeats/.cache/uv,uid=1000 \
    uv sync --locked

ENTRYPOINT ["uv", "run", "src/server.py"]
CMD ["--host", "0.0.0.0"]
EXPOSE 9009