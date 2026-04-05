from typing import List, Dict, Any
from .config import PromptConfig

try:
    from promptcfg.promptcfg_core import RustPromptBuilder
    HAS_RUST_CORE = True
except ImportError:
    HAS_RUST_CORE = False
    from jinja2 import Template

class PromptBuilder:
    def __init__(self, config: PromptConfig):
        self.config = config
        self._rust_builder = None
        self._rust_builder_length = 0
        if HAS_RUST_CORE:
            # Initialize the Rust engine with the compiled prompt list
            self._rust_builder = RustPromptBuilder(self.config.prompts)
            self._rust_builder_length = len(self.config.prompts)

    def build(self, tags: List[str], variables: Dict[str, Any], include_ids: List[str] = None, exclude_ids: List[str] = None, exclude_tags: List[str] = None) -> str:
        active_tags = set(tags)
        include_ids_set = set(include_ids) if include_ids else set()
        exclude_ids_set = set(exclude_ids) if exclude_ids else set()
        exclude_tags_set = set(exclude_tags) if exclude_tags else set()
        
        # We process variables here so the Python dictionary reference is updated,
        # which satisfies backwards compatibility with the original unit tests
        for part in self.config.prompts:
            if self._should_include(part, active_tags, include_ids_set, exclude_ids_set, exclude_tags_set):
                for var_def in part.variables:
                    if var_def.name not in variables and var_def.default is not None:
                        variables[var_def.name] = str(var_def.default)
                self._validate_variables(part, variables)

        # Check if the config prompts array has been dynamically mutated 
        # (e.g. appended to) after the builder was initialized.
        if HAS_RUST_CORE:
            if self._rust_builder is None or len(self.config.prompts) != self._rust_builder_length:
                self._rust_builder = RustPromptBuilder(self.config.prompts)
                self._rust_builder_length = len(self.config.prompts)

        if self._rust_builder is not None:
            # Delegate entirely to compiled Rust extension (zero-cost abstraction boundary)
            return self._rust_builder.build(
                tags=tags,
                variables=variables,
                include_ids=include_ids,
                exclude_ids=exclude_ids,
                exclude_tags=exclude_tags
            )
            
        # Fallback to pure Python if Rust wheel wasn't compiled for this platform
        active_tags = set(tags)
        include_ids_set = set(include_ids) if include_ids else set()
        exclude_ids_set = set(exclude_ids) if exclude_ids else set()
        exclude_tags_set = set(exclude_tags) if exclude_tags else set()
        
        parts = []

        for part in self.config.prompts:
            if self._should_include(part, active_tags, include_ids_set, exclude_ids_set, exclude_tags_set):
                for var_def in part.variables:
                    if var_def.name not in variables and var_def.default is not None:
                        variables[var_def.name] = str(var_def.default)

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
