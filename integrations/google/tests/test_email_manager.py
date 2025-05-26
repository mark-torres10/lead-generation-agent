import pytest
from unittest.mock import patch, MagicMock
from integrations.google.email_manager import EmailManager
from googleapiclient.errors import HttpError

@patch("integrations.google.email_manager.GoogleAPICore._get_service")
def test_send_email_success(mock_get_service):
    mock_service = MagicMock()
    mock_send = mock_service.users.return_value.messages.return_value.send
    mock_send.return_value.execute.return_value = {"id": "test-message-id"}
    mock_get_service.return_value = mock_service

    manager = EmailManager()
    result = manager.send_email(
        subject="Test",
        message="Body",
        recipients=["test@example.com"],
        sender="sender@example.com"
    )
    assert result == "test-message-id"

@patch("integrations.google.email_manager.GoogleAPICore._get_service")
def test_send_email_http_error(mock_get_service):
    class MockResp:
        reason = "Mocked reason"
        status = 400
    mock_service = MagicMock()
    mock_send = mock_service.users.return_value.messages.return_value.send
    mock_send.return_value.execute.side_effect = HttpError(resp=MockResp(), content=b"error")
    mock_get_service.return_value = mock_service

    manager = EmailManager()
    with pytest.raises(HttpError):
        manager.send_email(
            subject="Test",
            message="Body",
            recipients=["test@example.com"],
            sender="sender@example.com"
        ) 