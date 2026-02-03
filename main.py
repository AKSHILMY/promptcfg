import argparse
import sys
from prompter.config import PromptConfig
from prompter.builder import PromptBuilder

def main():
    parser = argparse.ArgumentParser(description='Build dynamic prompts.')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--tags', default='', help='Comma-separated list of tags to activate')
    parser.add_argument('--vars', default='', help='Comma-separated list of key=value variables')
    
    args = parser.parse_args()

    try:
        config = PromptConfig.load(args.config)
    except Exception as e:
        print(f"Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)

    tags = args.tags.split(',') if args.tags else []
    
    variables = {}
    if args.vars:
        for pair in args.vars.split(','):
            if '=' in pair:
                key, value = pair.split('=', 1)
                variables[key] = value

    builder = PromptBuilder(config)
    try:
        prompt = builder.build(tags, variables)
        print("--- Generated Prompt ---")
        print(prompt)
        print("------------------------")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
