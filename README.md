# USACO Benchmark Green Agent
This repository implements a green agent for the USACO Bchmark on  the [AgentBeats platform](https://agentbeats.dev/).

## Overview
The USACO Benchmark, introduced in “[Can Language Models Solve Olympiad Programming?](https://arxiv.org/abs/2404.10952)”, consists of 307 USA Computing Olympiad problems with unit tests, reference solutions, and official editorials. It evaluates an agent’s ability to solve complex algorithmic challenges efficiently under time and memory constraints.

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

For quick testing, run the following command
```bash
uv run test_client.py
```

## Running with Docker
```bash
# Build the image
docker build --platform linux/amd64 -t usaco-green-agent .

# Run the container
docker run -p 9009:9009 --name usaco-green-agent usaco-green-agent
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

- **Create a git tag** (e.g. `git tag v1.0 && git push origin v1.0`) → publishes version tags:
```
ghcr.io/<your-username>/usaco-green-agent:1.0
```

Once the workflow completes, find your Docker image in the Packages section (right sidebar of your repository). Configure the package visibility in package settings.

## References
- [AgentBeats Platform](https://agentbeats.dev/)
- [Arxiv Paper] [Can Language Models Solve Olympiad Programming?](https://arxiv.org/abs/2404.10952)
- [Original USACO Benchmark Dataset](https://drive.google.com/file/d/1z5ODOJMqyer1QxzYtEUZ2hbAx-7nU8Vi/view)
  - More information from the official [repo](https://github.com/princeton-nlp/USACO)
- [Compiled USACO Benchmark Dataset on Hugging Face](https://huggingface.co/datasets/dapumptu/usaco_benchmark)