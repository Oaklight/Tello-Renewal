"""Main entry point for Tello renewal system.

This module provides the main entry point for the CLI application,
handling command-line arguments and dispatching to appropriate handlers.
"""

import sys

from .cli.commands import create_cli
from .utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Main entry point for the application."""
    try:
        cli = create_cli()
        cli()
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
