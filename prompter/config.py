import yaml
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PromptPart:
    id: str
    text: str
    tags: List[str] = None
    default: bool = False

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class PromptConfig:
    version: str
    prompts: List[PromptPart]

    @classmethod
    def load(cls, path: str) -> 'PromptConfig':
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        from .ids import PromptID
        
        valid_ids = PromptID.all()
        prompts = []
        for p in data.get('prompts', []):
            part = PromptPart(**p)
            if part.id not in valid_ids:
                raise ValueError(f"Invalid prompt ID: '{part.id}'. Allowed IDs are defined in PromptID.")
            prompts.append(part)
            
        return cls(version=data.get('version', '1.0'), prompts=prompts)
