import base64
from typing import List, Optional
from email.message import EmailMessage
from googleapiclient.errors import HttpError

from integrations.google.google_api_core import GoogleAPICore

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

class EmailManager(GoogleAPICore):
    """
    Manages sending emails via the Gmail API using OAuth2 credentials.
    Requires credentials.json in the working directory.
    """
    def __init__(self, credentials_path: str = None, token_path: str = None):
        super().__init__(
            api_name="gmail",
            api_version="v1",
            scopes=SCOPES,
            credentials_path=credentials_path,
            token_path=token_path,
        )

    def validate_recipient_emails(self, emails: list[str]) -> list[str]:
        """
        Validate recipient emails.
        Args:
            emails: List of email addresses to validate
        Returns:
            List of valid email addresses

        Currently just returns the sandbox email, to guarantee that we
        only send to one email address.
        """
        # TODO: Implement email validation
        print(f"[STUB]: Validating recipient emails: {emails} -> mtorres.sandbox@gmail.com")
        return ["mtorres.sandbox@gmail.com"]

    def send_email(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        sender: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> str:
        """
        Send an email using the Gmail API.
        Args:
            subject: Email subject
            message: Email body (plain text)
            recipients: List of recipient email addresses
            sender: Sender email address
            cc: List of CC addresses (optional)
            bcc: List of BCC addresses (optional)
            attachments: List of file paths to attach (optional)
        Returns:
            The message ID of the sent email.
        Raises:
            HttpError if sending fails.
        """
        recipients = self.validate_recipient_emails(recipients)

        email_message = EmailMessage()
        email_message.set_content(message)
        email_message["To"] = ", ".join(recipients)
        email_message["From"] = sender
        email_message["Subject"] = subject
        if cc:
            email_message["Cc"] = ", ".join(cc)
        if bcc:
            email_message["Bcc"] = ", ".join(bcc)
        # Attachments not implemented in this stub
        encoded_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        try:
            send_message = self.service.users().messages().send(userId="me", body=create_message).execute()
            print(f"Message Id: {send_message['id']}")
            return send_message["id"]
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

if __name__ == "__main__":
    # Example usage: send a test email to mtorres.sandbox@gmail.com
    SUBJECT = "Test Email from EmailManager"
    BODY = "This is a test email sent using the Gmail API and EmailManager."
    TO = ["mtorres.sandbox@gmail.com"]
    FROM = "mtorres.sandbox@gmail.com"  # Must match authenticated user
    manager = EmailManager()
    print("Sending test email...")
    manager.send_email(subject=SUBJECT, message=BODY, recipients=TO, sender=FROM)
    print("Email sent.")
