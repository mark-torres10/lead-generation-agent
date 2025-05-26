import datetime
from typing import Optional
from googleapiclient.errors import HttpError

from integrations.google.google_api_core import GoogleAPICore

class CalendarManager(GoogleAPICore):
    """
    Manages Google Calendar API operations using OAuth2 credentials.
    """
    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        super().__init__(
            api_name="calendar",
            api_version="v3",
            credentials_path=credentials_path,
            token_path=token_path,
        )

    def list_upcoming_events(self, max_results: int = 10):
        """
        Lists the next `max_results` upcoming events from the user's primary calendar.
        """
        try:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            if not events:
                print("No upcoming events found.")
                return []
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(start, event.get("summary", "(No Title)"))
            return events
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def get_events_in_range(self, start: datetime.datetime, end: datetime.datetime):
        """
        Return all events in the user's primary calendar between start and end (inclusive).
        """
        try:
            # Convert to UTC and RFC3339 format with 'Z' suffix
            start_utc = start.astimezone(datetime.timezone.utc)
            end_utc = end.astimezone(datetime.timezone.utc)
            start_str = start_utc.isoformat().replace('+00:00', 'Z')
            end_str = end_utc.isoformat().replace('+00:00', 'Z')
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_str,
                    timeMax=end_str,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return events_result.get("items", [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def is_time_slot_free(self, start: datetime.datetime, end: datetime.datetime) -> bool:
        """
        Return True if the time slot is free (no overlapping events).
        """
        events = self.get_events_in_range(start, end)
        for event in events:
            # Check for overlap
            event_start = event["start"].get("dateTime")
            event_end = event["end"].get("dateTime")
            if event_start and event_end:
                event_start_dt = datetime.datetime.fromisoformat(event_start.replace("Z", "+00:00"))
                event_end_dt = datetime.datetime.fromisoformat(event_end.replace("Z", "+00:00"))
                if not (end <= event_start_dt or start >= event_end_dt):
                    return False
        return True

    def get_1on1_meetings(self, max_results: int = 50):
        """
        Return all upcoming events with '1:1' in the summary.
        """
        try:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                    q="1:1"
                )
                .execute()
            )
            return events_result.get("items", [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def validate_recipient_emails(self, emails: list[str]) -> list[str]:
        """
        Validate recipient emails for calendar invites.
        Args:
            emails: List of email addresses to validate
        Returns:
            List of valid email addresses

        Currently just returns the sandbox email, to guarantee that we
        only send to one email address.
        """
        # TODO: Implement email validation
        print(f"[STUB]: Validating recipient emails for calendar: {emails} -> mtorres.sandbox@gmail.com")
        return ["mtorres.sandbox@gmail.com"]

if __name__ == "__main__":
    manager = CalendarManager()
    print("Listing next 10 upcoming events:")
    manager.list_upcoming_events() 