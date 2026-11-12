"""Shared filesystem and Docker tools for the engineering crew."""

from pathlib import Path
from typing import Any, Callable
import shutil
import subprocess
import warnings

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


SANDBOX_DIR = Path(__file__).resolve().parents[1] / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


def reset_sandbox() -> None:
    """Wipe the sandbox and re-initialize it as a fresh uv project with gradio."""
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)
    SANDBOX_DIR.mkdir(parents=True)

    subprocess.run(
        ["uv", "init", "--bare", "--python", "3.13", "--no-workspace"],
        cwd=SANDBOX_DIR,
        check=True,
    )
    subprocess.run(["uv", "add", "gradio"], cwd=SANDBOX_DIR, check=True)


def _never_cache(*_args, **_kwargs) -> bool:
    return False


def prepare_sandbox(inputs: dict[str, Any]) -> dict[str, Any]:
    """Prepare a fresh sandbox before kickoff and preserve the supplied inputs."""
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
    reset_sandbox()
    return inputs


class _EmptyInput(BaseModel):
    """The list tool accepts no arguments."""


class _FilenameInput(BaseModel):
    filename: str = Field(..., description="The name of the file (e.g. solution.py).")


class _WriteInput(_FilenameInput):
    content: str = Field(..., description="The text content to write.")


class _SandboxTool(BaseTool):
    # Files change between calls; never return cached filesystem or execution results.
    cache_function: Callable[..., bool] = Field(default=_never_cache)


class ListSandboxFilesTool(_SandboxTool):
    name: str = "List Sandbox Files"
    description: str = (
        "List the filenames currently in the sandbox directory.\n"
        "\n"
        "Returns:\n"
        "    A newline-separated list of filenames, or a message if the\n"
        "    sandbox is empty."
    )
    args_schema: type[BaseModel] = _EmptyInput

    def _run(self) -> str:
        names = sorted(p.name for p in SANDBOX_DIR.iterdir())
        return "\n".join(names) if names else "The sandbox is empty."


class ReadSandboxFileTool(_SandboxTool):
    name: str = "Read Sandbox File"
    description: str = (
        "Read and return the text contents of a file in the sandbox directory.\n"
        "\n"
        "Args:\n"
        "    filename: The name of the file to read (e.g. \"solution.py\").\n"
        "Returns:\n"
        "    The file's contents, or a message if the file does not exist."
    )
    args_schema: type[BaseModel] = _FilenameInput

    def _run(self, filename: str) -> str:
        path = SANDBOX_DIR / filename
        if not path.is_file():
            return f"No such file in the sandbox: {filename}"
        return path.read_text()


class WriteSandboxFileTool(_SandboxTool):
    name: str = "Write Sandbox File"
    description: str = (
        "Write text to a file in the sandbox directory, replacing any existing\n"
        "file with the same name.\n"
        "\n"
        "Args:\n"
        "    filename: The name of the file to write (e.g. \"solution.py\").\n"
        "    content: The text content to write.\n"
        "Returns:\n"
        "    A confirmation message."
    )
    args_schema: type[BaseModel] = _WriteInput

    def _run(self, filename: str, content: str) -> str:
        path = SANDBOX_DIR / filename
        path.write_text(content)
        return f"Wrote {len(content)} characters to {filename}."


class RunSandboxPythonTool(_SandboxTool):
    name: str = "Run Sandbox Python File"
    description: str = (
        "Execute a Python file from the sandbox directory inside an ephemeral\n"
        "Docker container, with the sandbox mounted as the working directory,\n"
        "using `uv run` to run the code in the uv project.\n"
        "\n"
        "Returns the exit code, stdout, and stderr, clearly labeled. Note that\n"
        "Python's unittest module prints test results — including failures and\n"
        "tracebacks — to stderr by default, not stdout, so stderr is just as\n"
        "important as stdout for understanding what happened.\n"
        "\n"
        "Args:\n"
        "    filename: The name of the Python file to run (e.g. \"solution.py\").\n"
        "Returns:\n"
        "    A labeled block containing the exit code, stdout, and stderr."
    )
    args_schema: type[BaseModel] = _FilenameInput

    def _run(self, filename: str) -> str:
        try:
            result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{SANDBOX_DIR}:/workspace",
                    "-w", "/workspace",
                    "ghcr.io/astral-sh/uv:python3.13-bookworm-slim",
                    "uv", "run", filename,
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
            return (
                f"Exit code: {result.returncode}\n\n"
                f"--- stdout ---\n{result.stdout or '(empty)'}\n\n"
                f"--- stderr ---\n{result.stderr or '(empty)'}"
            )
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            return (
                "The script timed out after 300 seconds.\n\n"
                f"--- stdout so far ---\n{stdout or '(empty)'}\n\n"
                f"--- stderr so far ---\n{stderr or '(empty)'}"
            )
