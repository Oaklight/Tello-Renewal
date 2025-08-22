"""Email notification system for Tello renewal.

This module provides email notification functionality for renewal success,
failure, and other events using SMTP.
"""

import inspect
import smtplib
import ssl
from datetime import date, timedelta
from email.message import EmailMessage
from typing import Any, List, Optional

from ..core.models import AccountBalance, RenewalResult
from ..utils.config import NotificationConfig, SmtpConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


class EmailNotifier:
    """Enhanced email notification system for Tello renewal."""

    def __init__(
        self, smtp_config: SmtpConfig, notification_config: NotificationConfig
    ):
        """Initialize email notifier.

        Args:
            smtp_config: SMTP server configuration
            notification_config: Notification preferences
        """
        self.smtp_config = smtp_config
        self.notification_config = notification_config
        self._server: Optional[smtplib.SMTP] = None

    def __enter__(self):
        """Context manager entry - establish SMTP connection."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - close SMTP connection."""
        self.disconnect()

    def connect(self) -> None:
        """Establish SMTP connection and authenticate."""
        try:
            logger.info(
                f"Connecting to SMTP server {self.smtp_config.server}:{self.smtp_config.port}"
            )

            self._server = smtplib.SMTP(self.smtp_config.server, self.smtp_config.port)

            if self.smtp_config.use_tls:
                context = ssl.create_default_context()
                self._server.starttls(context=context)
                logger.debug("TLS encryption enabled")

            self._server.login(self.smtp_config.username, self.smtp_config.password)
            logger.info("SMTP authentication successful")

        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise

    def disconnect(self) -> None:
        """Close SMTP connection."""
        if self._server:
            try:
                self._server.quit()
                logger.debug("SMTP connection closed")
            except Exception as e:
                logger.warning(f"Error closing SMTP connection: {e}")
            finally:
                self._server = None

    def _create_message(
        self, subject: str, body: str, recipients: List[str]
    ) -> EmailMessage:
        """Create email message.

        Args:
            subject: Email subject
            body: Email body content
            recipients: List of recipient email addresses

        Returns:
            Configured EmailMessage object
        """
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.smtp_config.from_email
        message["To"] = ", ".join(recipients)
        message.set_content(body)

        return message

    def _send_message(self, message: EmailMessage) -> None:
        """Send email message.

        Args:
            message: Email message to send

        Raises:
            RuntimeError: If not connected to SMTP server
        """
        if not self._server:
            raise RuntimeError("Not connected to SMTP server. Call connect() first.")

        try:
            self._server.send_message(message)
            logger.info(f"Email sent successfully to {message['To']}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    def send_success_notification(self, email: str, result: RenewalResult) -> None:
        """Send renewal success notification.

        Args:
            email: Tello account email
            result: Renewal result with success details
        """
        if (
            not self.notification_config.email_enabled
            or not self.notification_config.send_on_success
        ):
            logger.debug("Success notifications disabled, skipping email")
            return

        if not self.notification_config.recipients:
            logger.warning("No email recipients configured")
            return

        subject = "✅ Tello Plan Renewed Successfully"

        # Calculate next renewal date (typically 30 days from today)
        next_renewal = date.today() + timedelta(days=30)

        body_template = f"""Hi there,

Great news! Your Tello account ({email}) was renewed successfully.

{self._format_balance_info(result.new_balance) if result.new_balance else ""}Renewal completed at: {result.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
Next renewal scheduled for: {next_renewal.strftime("%B %d, %Y")}

You don't need to take any action. Your service will continue uninterrupted.

Best regards,
Tello Auto-Renewal System"""

        body = inspect.cleandoc(body_template)

        message = self._create_message(
            subject, body, self.notification_config.recipients
        )
        self._send_message(message)

    def send_failure_notification(self, email: str, error: str) -> None:
        """Send renewal failure notification.

        Args:
            email: Tello account email
            error: Error message describing the failure
        """
        if (
            not self.notification_config.email_enabled
            or not self.notification_config.send_on_failure
        ):
            logger.debug("Failure notifications disabled, skipping email")
            return

        if not self.notification_config.recipients:
            logger.warning("No email recipients configured")
            return

        subject = "❌ Tello Plan Renewal Failed - Action Required"

        body_template = f"""Hi there,

Unfortunately, your Tello account ({email}) failed to renew automatically.

Error details:
{error}

IMPORTANT: Please log in to your Tello account and complete the renewal manually
as soon as possible to avoid service interruption.

Login here: https://tello.com/account/login

If you continue to experience issues, please contact Tello customer support.

Best regards,
Tello Auto-Renewal System"""

        body = inspect.cleandoc(body_template)

        message = self._create_message(
            subject, body, self.notification_config.recipients
        )
        self._send_message(message)

    def send_not_due_notification(self, email: str, days_until: int) -> None:
        """Send notification when renewal is not yet due.

        Args:
            email: Tello account email
            days_until: Number of days until renewal is due
        """
        if (
            not self.notification_config.email_enabled
            or not self.notification_config.send_on_not_due
        ):
            logger.debug("Not-due notifications disabled, skipping email")
            return

        if not self.notification_config.recipients:
            logger.warning("No email recipients configured")
            return

        subject = f"ℹ️ Tello Renewal Check - {days_until} Days Remaining"

        body_template = f"""Hi there,

This is a status update for your Tello account ({email}).

Your plan renewal is not yet due. You have {days_until} days remaining
before the next renewal is required.

The auto-renewal system will automatically renew your plan when it's due.
No action is required from you at this time.

Best regards,
Tello Auto-Renewal System"""

        body = inspect.cleandoc(body_template)

        message = self._create_message(
            subject, body, self.notification_config.recipients
        )
        self._send_message(message)

    def send_test_notification(self) -> None:
        """Send test notification to verify email configuration."""
        if not self.notification_config.email_enabled:
            logger.debug("Email notifications disabled, skipping test")
            return

        if not self.notification_config.recipients:
            logger.warning("No email recipients configured")
            return

        subject = "🧪 Tello Auto-Renewal Test Email"

        body_template = f"""Hi there,

This is a test email from the Tello Auto-Renewal system.

If you're receiving this message, your email configuration is working correctly.

Configuration details:
• SMTP Server: {self.smtp_config.server}:{self.smtp_config.port}
• From Address: {self.smtp_config.from_email}
• TLS Enabled: {self.smtp_config.use_tls}
• Recipients: {", ".join(self.notification_config.recipients)}

Best regards,
Tello Auto-Renewal System"""

        body = inspect.cleandoc(body_template)

        message = self._create_message(
            subject, body, self.notification_config.recipients
        )
        self._send_message(message)

    def send_reminder_notification(self, email: str, days_until: int) -> None:
        """Send renewal reminder notification.

        Args:
            email: Tello account email
            days_until: Number of days until renewal
        """
        if not self.notification_config.email_enabled:
            logger.debug("Email notifications disabled, skipping reminder")
            return

        if not self.notification_config.recipients:
            logger.warning("No email recipients configured")
            return

        subject = f"⏰ Tello Renewal Reminder - {days_until} Days Until Renewal"

        body_template = f"""Hi there,

This is a friendly reminder about your upcoming Tello plan renewal.

Account: {email}
Days until renewal: {days_until}

The auto-renewal system will automatically handle the renewal when it's due.
Please ensure your payment method is up to date in your Tello account.

Login here: https://tello.com/account/login

Best regards,
Tello Auto-Renewal System"""

        body = inspect.cleandoc(body_template)

        message = self._create_message(
            subject, body, self.notification_config.recipients
        )
        self._send_message(message)

    def _format_balance_info(self, balance: AccountBalance) -> str:
        """Format account balance information for email display.

        Args:
            balance: Account balance information

        Returns:
            Formatted balance string with proper indentation
        """
        balance_template = f"""Your new account balance:
• Data: {balance.data}
• Minutes: {balance.minutes}
• Texts: {balance.texts}

"""
        return inspect.cleandoc(balance_template) + "\n\n"


def create_email_notifier(
    smtp_config: SmtpConfig, notification_config: NotificationConfig
) -> EmailNotifier:
    """Factory function to create an EmailNotifier instance.

    Args:
        smtp_config: SMTP configuration
        notification_config: Notification configuration

    Returns:
        Configured EmailNotifier instance
    """
    return EmailNotifier(smtp_config, notification_config)
