# USACO Benchmark Green Agent

## Overview

This repository implements an AgentBeats green agent for the USACO benchmark. The benchmark was introduced in the paper “[Can Language Models Solve Olympiad Programming?](https://arxiv.org/abs/2404.10952)”

## Project Structure

```
src/
├─ server.py      # Server setup and agent card configuration
├─ executor.py    # A2A request handling
├─ agent.py       # Green agent implementation
├─ messenger.py   # A2A messaging utilities
├─ judge.py       # USACO judge implementation
└─ evaluator.py   # USACO evaluator implementation
.github/
└─ workflows/
   └─ test-and-publish.yml # CI workflow
tests/
└─ test_agent.py  # Agent tests
parse_dataset.py  # Dataset preprocessing
test_client.py    # Local test client
pyproject.toml    # Python dependencies
Dockerfile        # Docker configuration
```

## Getting Started
1. Clone the repo:
   ```bash
   git clone https://github.com/NTU-P04922004/usaco-green-agent
   cd usaco-green-agent
   ```

2. Set environment variables
- Set `DATASET_ID` environment variable to the Hugging Face dataset ID `dapumptu/usaco_benchmark`

## Running Locally

```bash
# Install dependencies
uv sync

# Run the server
uv run src/server.py
```

## Running with Docker

```bash
# Build the image
docker build -t usaco-green-agent .

# Run the container
docker run -p 9009:9009 usaco-green-agent
```

## Testing

Run A2A conformance tests against your agent.

```bash
# Install test dependencies
uv sync --extra test

# Start your agent (uv or docker; see above)

# Run tests against your running agent URL
uv run pytest --agent-url http://localhost:9009
```

## Publishing

The repository includes a GitHub Actions workflow that automatically builds, tests, and publishes a Docker image of your agent to GitHub Container Registry.

If your agent needs API keys or other secrets, add them in Settings → Secrets and variables → Actions → Repository secrets. They'll be available as environment variables during CI tests.

- **Push to `main`** → publishes `latest` tag:
```
ghcr.io/<your-username>/usaco-green-agent:latest
```

- **Create a git tag** (e.g. `git tag v1.0.0 && git push origin v1.0.0`) → publishes version tags:
```
ghcr.io/<your-username>/usaco-green-agent:1.0.0
ghcr.io/<your-username>/usaco-green-agent:1
```

Once the workflow completes, find your Docker image in the Packages section (right sidebar of your repository). Configure the package visibility in package settings.

> **Note:** Organization repositories may need package write permissions enabled manually (Settings → Actions → General). Version tags must follow [semantic versioning](https://semver.org/) (e.g., `v1.0.0`).
