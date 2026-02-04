# Prompter

A dynamic prompt building library for LLM applications. It allows you to define prompts in YAML, manage variables, tags, and inheritance, and build them dynamically at runtime.

## Installation

Requires Python >= 3.12.

```bash
pip install prompter
```

## Development Setup

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
```

## Usage

### CLI

Initialize a new configuration:

```bash
prompter init
```

This creates a `prompter.yaml` file in your current directory.

Build a prompt from the CLI:

```bash
prompter build --tags python,web --vars user=Alice
```

### Python API

```python
from prompter.config import PromptConfig
from prompter.builder import PromptBuilder

# Load config
config = PromptConfig.load("prompter.yaml")

# Create builder
builder = PromptBuilder(config)

# Build prompt
prompt = builder.build(
    tags=["python", "web"], 
    variables={"user": "Alice"}
)

print(prompt)
```
