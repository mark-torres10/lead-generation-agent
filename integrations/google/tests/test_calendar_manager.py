import pytest
from unittest.mock import patch, MagicMock
from integrations.google.calendar_manager import CalendarManager

@patch("integrations.google.calendar_manager.GoogleAPICore._get_service")
def test_list_upcoming_events_returns_events(mock_get_service):
    # Mock the service.events().list().execute() chain
    mock_service = MagicMock()
    mock_events = [
        {"start": {"dateTime": "2024-06-01T10:00:00Z"}, "summary": "Event 1"},
        {"start": {"dateTime": "2024-06-02T11:00:00Z"}, "summary": "Event 2"},
    ]
    mock_service.events.return_value.list.return_value.execute.return_value = {"items": mock_events}
    mock_get_service.return_value = mock_service

    manager = CalendarManager()
    events = manager.list_upcoming_events(max_results=2)
    assert isinstance(events, list)
    assert len(events) == 2
    assert events[0]["summary"] == "Event 1"

@patch("integrations.google.calendar_manager.GoogleAPICore._get_service")
def test_list_upcoming_events_no_events(mock_get_service, capsys):
    mock_service = MagicMock()
    mock_service.events.return_value.list.return_value.execute.return_value = {"items": []}
    mock_get_service.return_value = mock_service

    manager = CalendarManager()
    events = manager.list_upcoming_events(max_results=2)
    assert events == []
    captured = capsys.readouterr()
    assert "No upcoming events found." in captured.out 