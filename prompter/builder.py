from typing import List, Dict, Any
from jinja2 import Template
from .config import PromptConfig

class PromptBuilder:
    def __init__(self, config: PromptConfig):
        self.config = config

    def build(self, tags: List[str], variables: Dict[str, Any]) -> str:
        active_tags = set(tags)
        parts = []

        for part in self.config.prompts:
            if self._should_include(part, active_tags):
                for var_def in part.variables:
                    if var_def.name not in variables and var_def.default is not None:
                        variables[var_def.name] = var_def.default

                self._validate_variables(part, variables)
                template = Template(part.text)
                rendered_text = template.render(variables)
                parts.append(rendered_text)

        return "\n\n".join(parts)

    def _validate_variables(self, part, variables):
        for var_def in part.variables:
            if var_def.required and var_def.name not in variables:
                raise ValueError(f"Missing required variable '{var_def.name}' for prompt '{part.id}'")

    def _should_include(self, part, active_tags):
        if part.default:
            return True
        
        for tag in part.tags:
            if tag in active_tags:
                return True
        
        return False
