class PromptID:
    CORE_IDENTITY = "core_identity"
    USER_CONTEXT = "user_context"
    CODING_GENERAL = "coding_general"
    PYTHON_RULES = "python_rules"
    GO_RULES = "go_rules"
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_WRITING = "technical_writing"
    FORMAT_JSON = "format_json"
    FORMAT_MARKDOWN = "format_markdown"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    PYTHON_EXAMPLES = "python_examples"

    ROLE_DEFINITION = "role_definition"
    PYTHON_EXPERT = "python_expert"
    GO_EXPERT = "go_expert"
    CONCISE_RESPONSE = "concise_response"

    @classmethod
    def all(cls):
        return {
            v for k, v in vars(cls).items() 
            if not k.startswith('_') and isinstance(v, str)
        }
