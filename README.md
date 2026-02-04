# prompt-config

[![PyPI version](https://badge.fury.io/py/prompt-config.svg)](https://badge.fury.io/py/prompt-config)
[![Python Versions](https://img.shields.io/pypi/pyversions/prompt-config.svg)](https://pypi.org/project/prompt-config/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**prompt-config** is a dynamic prompt building library designed for LLM applications. It allows you to define complex prompts in a structured YAML configuration, manage dynamic variables with Jinja2 templating, and construct prompts at runtime using a powerful tagging and filtering system.

Perfect for managing prompts as code, enabling environment-specific prompts, and ensuring reproducibility in your AI applications.

---

## Features

- **YAML Configuration**: Centralize your prompt definitions in a clean, readable YAML file.
- **Dynamic Variables**: Use **Jinja2** syntax (`{{ variable }}`) for dynamic content insertion.
- **Tag-Based Composition**: conditionally include or exclude prompt parts based on tags (e.g., `dev`, `prod`, `python`, `web`).
- **Validation**: Enforce required variables and provide default values.
- **CLI Tool**: Built-in `promptcfg` CLI for easy integration into scripts and CI/CD pipelines.
- **Python API**: seamless integration into your Python applications.

## Installation

Requires **Python 3.11** or higher.

```bash
pip install prompt-config
```

## Quick Start

### 1. Initialize Configuration

Create a starter `promptcfg.yaml` file in your current directory:

```bash
promptcfg init
```

This will generate a file similar to:

```yaml
version: "1.0"
prompts:
  - id: "system_intro"
    text: "You are a helpful AI assistant named {{ assistant_name }}."
    default: true
    variables:
      - name: "assistant_name"
        default: "Prompter"

  - id: "coding_capabilities"
    text: "You are an expert in {{ language }} programming."
    tags: ["coding"]
    variables:
      - name: "language"
        required: true
```

### 2. Build via CLI

Generate a prompt by activating specific tags and passing variables:

```bash
promptcfg build --tags coding --vars assistant_name=Jarvis,language=Python
```

**Output:**
```text
--- Generated Prompt ---
You are a helpful AI assistant named Jarvis.
You are an expert in Python programming.
------------------------
```

### 3. Build via Python API

Integrate `prompt-config` directly into your application:

```python
from promptcfg.config import PromptConfig
from promptcfg.builder import PromptBuilder

# Load the configuration
config = PromptConfig.load("promptcfg.yaml")

# Initialize the builder
builder = PromptBuilder(config)

# Build the prompt
prompt = builder.build(
    tags=["coding"],
    variables={
        "assistant_name": "Jarvis",
        "language": "Python"
    }
)

print(prompt)
```

## CLI Usage

The `promptcfg` generic command line interface supports the following subcommands:

- `init`: Create a generic configuration file.
- `build`: Construct a prompt based on tags and variables.

### Build Options

| Option | Description |
|--------|-------------|
| `--config` | Path to the YAML config file (default: `promptcfg.yaml`) |
| `--tags` | Comma-separated list of tags to include (e.g., `dev,test`) |
| `--vars` | Key-value pairs for variables (e.g., `key=value,foo=bar`) |
| `--include-ids` | Explicitly include specific prompt blocks by ID |
| `--exclude-ids` | Explicitly exclude specific prompt blocks by ID |
| `--exclude-tags` | Exclude prompt blocks matching these tags |
| `--list-prompts`| List all available prompt IDs and their status |

```bash
# Example: Build with exclusions
promptcfg build --tags all --exclude-tags deprecated --vars user_id=123
```

## Development

If you want to contribute or modify the library:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AKSHILMY/prompter.git
   cd prompter
   ```

2. **Set up a virtual environment:**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

3. **Install in editable mode:**
   ```bash
   pip install -e "."
   ```

4. **Run Tests:**
   ```bash
   python -m unittest discover tests
   ```

## License

This project is licensed under the terms of the [Apache License 2.0](LICENSE).
