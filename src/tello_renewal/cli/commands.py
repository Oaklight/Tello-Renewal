"""CLI commands for Tello renewal system.

This module provides a simplified command-line interface using argparse.
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from .. import __version__
from ..core.models import RenewalStatus
from ..core.renewer import RenewalEngine
from ..notification.email import EmailNotifier
from ..utils.config import Config, create_example_config, get_settings
from ..utils.logging import configure_logging, get_logger

logger = get_logger(__name__)
# Type alias for argparse.Namespace
Args = argparse.Namespace


def setup_logging_and_config(config_path: Optional[str], verbose: bool) -> Config:
    """Set up logging and load configuration.

    Args:
        config_path: Path to configuration file
        verbose: Enable verbose logging

    Returns:
        Loaded configuration

    Raises:
        SystemExit: If configuration loading fails
    """
    try:
        config = get_settings(config_path)

        # Override log level if verbose
        if verbose:
            config.logging.level = "DEBUG"

        configure_logging(config.logging)
        return config

    except FileNotFoundError as e:
        print(f"Configuration file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Invalid configuration: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_renew(args: Args) -> None:
    """Execute plan renewal."""
    config = setup_logging_and_config(args.config, args.verbose)

    logger.info("Starting Tello plan renewal")

    try:
        # Create renewal engine
        engine = RenewalEngine(config, dry_run=args.dry_run)

        # Execute renewal with force flag
        result = engine.execute_renewal(force=getattr(args, 'force', False))

        # Send notifications if configured
        if config.notifications.email_enabled:
            with EmailNotifier(config.smtp, config.notifications) as notifier:
                if result.status == RenewalStatus.SUCCESS:
                    notifier.send_success_notification(config.tello.email, result)
                elif result.status == RenewalStatus.FAILED:
                    notifier.send_failure_notification(
                        config.tello.email, result.error or "Unknown error"
                    )
                elif (
                    result.status == RenewalStatus.NOT_DUE
                    and config.notifications.send_on_not_due
                ):
                    # Calculate days until renewal
                    summary = engine.get_account_summary()
                    notifier.send_not_due_notification(
                        config.tello.email, summary.days_until_renewal
                    )

        # Print result
        print(f"Status: {result.status.value}")
        print(f"Message: {result.message}")
        if result.new_balance:
            print(f"New balance: {result.new_balance}")
        if result.duration_seconds:
            print(f"Duration: {result.duration_seconds:.2f} seconds")

        # Set exit code based on result
        if result.status == RenewalStatus.SUCCESS:
            sys.exit(0)
        elif result.status == RenewalStatus.NOT_DUE:
            sys.exit(6)  # Not due for renewal
        elif result.status == RenewalStatus.SKIPPED:
            sys.exit(7)  # Skipped due to cache
        elif result.status == RenewalStatus.FAILED:
            sys.exit(5)  # Renewal failed
        else:
            sys.exit(1)  # General error

    except Exception as e:
        logger.error(f"Renewal failed with exception: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args: Args) -> None:
    """Check account status and renewal information."""
    config = setup_logging_and_config(args.config, args.verbose)

    try:
        engine = RenewalEngine(config, dry_run=True)
        summary = engine.get_account_summary()

        print(f"Account: {summary.email}")
        print(f"Renewal date: {summary.renewal_date}")
        print(f"Days until renewal: {summary.days_until_renewal}")
        print(f"Renewal due: {'Yes' if summary.is_renewal_due else 'No'}")

        print("\nCurrent Balance:")
        print(f"  Data: {summary.current_balance.data}")
        print(f"  Minutes: {summary.current_balance.minutes}")
        print(f"  Texts: {summary.current_balance.texts}")

        print("\nPlan Balance (will be added on renewal):")
        print(f"  Data: {summary.plan_balance.data}")
        print(f"  Minutes: {summary.plan_balance.minutes}")
        print(f"  Texts: {summary.plan_balance.texts}")

        print("\nBalance After Renewal:")
        print(f"  Data: {summary.new_balance.data}")
        print(f"  Minutes: {summary.new_balance.minutes}")
        print(f"  Texts: {summary.new_balance.texts}")

        # Exit with appropriate code for automation
        if summary.is_renewal_due:
            print("\n⚠️  Renewal is due!")
            sys.exit(0)  # Due for renewal
        else:
            print("\n✅ Renewal is not yet due")
            sys.exit(6)  # Not due for renewal

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_email_test(args: Args) -> None:
    """Send test email notification."""
    config = setup_logging_and_config(args.config, args.verbose)

    if not config.notifications.email_enabled:
        print("Email notifications are disabled in configuration", file=sys.stderr)
        sys.exit(2)

    if not config.notifications.recipients:
        print("No email recipients configured", file=sys.stderr)
        sys.exit(2)

    try:
        with EmailNotifier(config.smtp, config.notifications) as notifier:
            notifier.send_test_notification()

        print("Test email sent successfully")
        print(f"Recipients: {', '.join(config.notifications.recipients)}")

    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        print(f"Error sending test email: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_config_init(args: Args) -> None:
    """Create example configuration file."""
    output = Path(args.output)

    # If using default output, create directories if needed
    if args.output == "config.toml" and not output.parent.exists():
        # Check if we should create in a standard location
        if not output.exists():
            # Create parent directories if needed
            output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists():
        response = input(
            f"Configuration file {output} already exists. Overwrite? (y/N): "
        )
        if response.lower() not in ["y", "yes"]:
            print("Configuration creation cancelled")
            return

    try:
        # Create parent directories if they don't exist
        output.parent.mkdir(parents=True, exist_ok=True)

        create_example_config(output)
        print(f"Example configuration created: {output}")
        print(
            "Please edit the configuration file with your settings before running renewal."
        )
        print("\nThe configuration will be automatically found in this location.")
        print("You can also place it in:")
        print(
            "  - Current directory: config.toml, tello_renewal.toml, or tello-renewal.toml"
        )
        print("  - ~/.config/tello-renewal/config.toml")
        print("  - .tello-renewal/config.toml")

    except Exception as e:
        print(f"Error creating configuration: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_config_validate(args: Args) -> None:
    """Validate configuration file."""
    try:
        config = setup_logging_and_config(args.config, args.verbose)
        print("Configuration is valid")

        # Show some key settings
        print(f"Tello account: {config.tello.email}")
        print(
            f"Browser: {config.browser.browser_type} (headless: {config.browser.headless})"
        )
        print(f"SMTP server: {config.smtp.server}:{config.smtp.port}")
        print(
            f"Email notifications: {'enabled' if config.notifications.email_enabled else 'disabled'}"
        )
        print(f"Recipients: {len(config.notifications.recipients)}")

    except Exception as e:
        print(f"Configuration validation failed: {e}", file=sys.stderr)
        sys.exit(2)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Tello mobile plan automatic renewal system"
    )

    # Global options
    parser.add_argument("--config", "-c", type=str, help="Path to configuration file")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Renew command
    renew_parser = subparsers.add_parser("renew", help="Execute plan renewal")
    renew_parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Test renewal process without actually renewing",
    )
    renew_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force renewal ignoring cached due date (respects --dry-run)",
    )
    renew_parser.set_defaults(func=cmd_renew)

    # Status command
    status_parser = subparsers.add_parser(
        "status", help="Check account status and renewal information"
    )
    status_parser.set_defaults(func=cmd_status)

    # Email test command
    email_test_parser = subparsers.add_parser(
        "email-test", help="Send test email notification"
    )
    email_test_parser.set_defaults(func=cmd_email_test)

    # Config init command
    config_init_parser = subparsers.add_parser(
        "config-init", help="Create example configuration file"
    )
    config_init_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="config.toml",
        help="Output path for configuration file",
    )
    config_init_parser.set_defaults(func=cmd_config_init)

    # Config validate command
    config_validate_parser = subparsers.add_parser(
        "config-validate", help="Validate configuration file"
    )
    config_validate_parser.set_defaults(func=cmd_config_validate)

    return parser


def create_cli() -> Callable[[], None]:
    """Create and return the CLI function for compatibility.

    Returns:
        Callable that runs the CLI
    """

    def cli() -> None:
        parser = create_parser()
        args = parser.parse_args()

        if not hasattr(args, "func"):
            parser.print_help()
            sys.exit(1)

        args.func(args)

    return cli


def main() -> None:
    """Main CLI entry point."""
    cli = create_cli()
    cli()


if __name__ == "__main__":
    main()
