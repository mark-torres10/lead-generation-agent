import pytest
from unittest.mock import MagicMock, patch
from slack_sdk.errors import SlackApiError
from integrations.slack_manager import SlackManager

@pytest.fixture
def mock_client():
    return MagicMock()

@pytest.fixture
def slack_manager(mock_client):
    return SlackManager(client=mock_client)

def test_get_channel_id_success(slack_manager, mock_client):
    # Setup
    mock_client.conversations_list.return_value = {
        "channels": [
            {"name": "test-channel", "id": "C123"},
            {"name": "other", "id": "C999"},
        ],
        "response_metadata": {"next_cursor": ""}
    }
    # Act
    result = slack_manager.get_channel_id("test-channel")
    expected_result = "C123"
    # Assert
    assert result == expected_result
    # Test caching
    result2 = slack_manager.get_channel_id("test-channel")
    assert result2 == expected_result
    # Should only call API once for cached channel
    assert mock_client.conversations_list.call_count == 1

def test_get_channel_id_not_found(slack_manager, mock_client):
    mock_client.conversations_list.return_value = {
        "channels": [],
        "response_metadata": {"next_cursor": ""}
    }
    with pytest.raises(ValueError) as exc:
        slack_manager.get_channel_id("missing")
    assert "not found" in str(exc.value)

def test_send_message_success(slack_manager, mock_client):
    # Setup
    slack_manager._channel_cache["foo"] = "CFOO"
    mock_client.chat_postMessage.return_value = {"ts": "123.456"}
    # Act
    ts = slack_manager.send_message("foo", "Title", "Body")
    expected_result = "123.456"
    # Assert
    assert ts == expected_result
    mock_client.chat_postMessage.assert_called_once()
    args, kwargs = mock_client.chat_postMessage.call_args
    assert kwargs["channel"] == "CFOO"
    assert kwargs["text"].startswith("*Title*")
    assert "Body" in kwargs["text"]

def test_send_message_channel_lookup_and_error(slack_manager, mock_client):
    # Simulate channel not found
    mock_client.conversations_list.return_value = {"channels": [], "response_metadata": {"next_cursor": ""}}
    with pytest.raises(ValueError):
        slack_manager.send_message("nope", "Title", "Body")

def test_send_message_slack_api_error(slack_manager, mock_client):
    # Setup
    slack_manager._channel_cache["foo"] = "CFOO"
    mock_client.chat_postMessage.side_effect = SlackApiError(message="fail", response={})
    with pytest.raises(SlackApiError):
        slack_manager.send_message("foo", "Title", "Body") 