# CrewAI Engineering Team

A CrewAI project using JSON-first configuration to turn requirements into a working Python application. The engineering lead designs the solution and assigns work, the backend engineer implements the Python logic, the frontend engineer builds and validates a Gradio UI, and the test engineer writes and runs backend unit tests and fixes defects. The agents work sequentially in a shared sandbox.

> **Lab / experimentation project.** This repo is a learning lab, not a production system. It is based on the CrewAI week of 
> the [Master AI Agentic Engineering - build autonomous AI Agents](https://github.com/ed-donner/agents/tree/main/3_crewai) by 
> Ed Donner. 
>
> Author: Sebastian Castañeda.


## Project Structure

- `agents/` - Agent definitions (JSONC)
- `crew.jsonc` - Crew definition with tasks and configuration
- `tools/` - Custom tools (Python)
- `knowledge/` - Knowledge files for agents

> **Note:** `custom:<name>` tool references execute `tools/<name>.py` as local
> Python code when the crew loads. Only run crew projects from sources you
> trust.


## Commands

Prerequisites: Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Docker with its daemon running.

### Initialize

Clone the repository and install the dependencies. If you already have a checkout, start in the project root and skip the first two commands.

```bash
git clone https://github.com/seba3c/engineering_team.git
cd engineering_team
uv python install 3.13
uv sync --python 3.13
touch .env
```

Edit `.env` in the project root, preserving any existing entries, and set your OpenAI API key and enable tracing:

```dotenv
OPENAI_API_KEY=your_openai_api_key
CREWAI_TRACING_ENABLED=true
```

### Run locally

From the project root, check that Docker is available and run the crew:

```bash
docker info
uv run crewai run
```

Each run recreates `sandbox/`, where the agents generate the application and tests. After a successful run, launch the generated Gradio UI from the project root:

```bash
cd sandbox
uv run python app.py
```
