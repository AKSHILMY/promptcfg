from typing import List, Dict, Any
from jinja2 import Template
from .config import PromptConfig

class PromptBuilder:
    def __init__(self, config: PromptConfig):
        self.config = config

    def build(self, tags: List[str], variables: Dict[str, Any], include_ids: List[str] = None, exclude_ids: List[str] = None, exclude_tags: List[str] = None) -> str:
        active_tags = set(tags)
        include_ids_set = set(include_ids) if include_ids else set()
        exclude_ids_set = set(exclude_ids) if exclude_ids else set()
        exclude_tags_set = set(exclude_tags) if exclude_tags else set()
        
        parts = []

        for part in self.config.prompts:
            if self._should_include(part, active_tags, include_ids_set, exclude_ids_set, exclude_tags_set):
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

    def _should_include(self, part, active_tags, include_ids, exclude_ids, exclude_tags):
        
        if part.id in exclude_ids:
            return False
        
        
        if part.id in include_ids:
            return True
            
        
        if part.tags and any(tag in exclude_tags for tag in part.tags):
            return False
        
        
        if part.tags and any(tag in active_tags for tag in part.tags):
            return True
        
        
        return part.default
