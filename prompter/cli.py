import argparse
import sys
import os
from prompter.config import PromptConfig
from prompter.builder import PromptBuilder

def init_command(args):
    target_file = "prompter.yaml"
    if os.path.exists(target_file) and not args.force:
        print(f"Error: {target_file} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    default_content = """version: "1.0"
prompts:
  - id: "example_prompt"
    text: "This is an example prompt with a variable: {{ name }}"
    variables:
      - name: "name"
        description: "The name of the user"
        default: "User"
    tags: ["example"]
    default: true
"""
    with open(target_file, "w") as f:
        f.write(default_content)
    print(f"Created {target_file}")

def build_command(args):
    try:
        config = PromptConfig.load(args.config)
    except Exception as e:
        print(f"Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)

    if args.list_prompts:
        print("Available Prompts:")
        print(f"{'ID':<20} {'Default':<10} {'Tags'}")
        print("-" * 50)
        for p in config.prompts:
            tags_str = ", ".join(p.tags) if p.tags else ""
            print(f"{p.id:<20} {str(p.default):<10} {tags_str}")
        return

    tags = args.tags.split(',') if args.tags else []
    include_ids = args.include_ids.split(',') if args.include_ids else []
    exclude_ids = args.exclude_ids.split(',') if args.exclude_ids else []
    exclude_tags = args.exclude_tags.split(',') if args.exclude_tags else []
    
    variables = {}
    if args.vars:
        for pair in args.vars.split(','):
            if '=' in pair:
                key, value = pair.split('=', 1)
                variables[key] = value

    builder = PromptBuilder(config)
    try:
        prompt = builder.build(
            tags=tags, 
            variables=variables,
            include_ids=include_ids,
            exclude_ids=exclude_ids,
            exclude_tags=exclude_tags
        )
        print("--- Generated Prompt ---")
        print(prompt)
        print("------------------------")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Prompter: Dynamic Prompt Builder')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    
    parser_init = subparsers.add_parser('init', help='Initialize a new prompter configuration')
    parser_init.add_argument('--force', action='store_true', help='Overwrite existing config file')

    
    parser_build = subparsers.add_parser('build', help='Build a prompt')
    parser_build.add_argument('--config', default='prompter.yaml', help='Path to configuration file')
    parser_build.add_argument('--tags', default='', help='Comma-separated list of tags to activate')
    parser_build.add_argument('--vars', default='', help='Comma-separated list of key=value variables')
    parser_build.add_argument('--include-ids', default='', help='Comma-separated list of IDs to explicitly include')
    parser_build.add_argument('--exclude-ids', default='', help='Comma-separated list of IDs to explicitly exclude')
    parser_build.add_argument('--exclude-tags', default='', help='Comma-separated list of tags to exclude')
    parser_build.add_argument('--list-prompts', action='store_true', help='List all available prompts and exit')

    
    
    
    
    
    args = parser.parse_args()

    if args.command == 'init':
        init_command(args)
    elif args.command == 'build':
        build_command(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
