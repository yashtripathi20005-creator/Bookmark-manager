"""
Bookmark Manager with Tags - Main Entry Point
A powerful bookmark management tool with tagging support
"""
import sys
from cli import cli


def main():
    """Main entry point for the application"""
    try:
        cli()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
