#!/usr/bin/env python3
"""
Google Calendar Integration
Handles authentication and data retrieval from Google Calendar API
"""

import logging
import os
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendarIntegration:
    """Google Calendar API integration for ETL data ingestion"""

    def __init__(
        self, credentials_file: str = "credentials.json", token_file: str = "token.json"
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.creds = None

    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API"""
        try:
            # The file token.json stores the user's access and refresh tokens.
            if os.path.exists(self.token_file):
                self.creds = Credentials.from_authorized_user_file(
                    self.token_file, SCOPES
                )

            # If there are no (valid) credentials available, let the user log in.
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(
                            f"Credentials file not found: {self.credentials_file}"
                        )
                        logger.info(
                            "Please download credentials from Google Cloud Console"
                        )
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(self.token_file, "w") as token:
                    token.write(self.creds.to_json())

            # Build the service
            self.service = build("calendar", "v3", credentials=self.creds)
            logger.info("Successfully authenticated with Google Calendar")
            return True

        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar: {e}")
            return False

    def get_meetings(
        self,
        start_date: datetime,
        end_date: datetime,
        calendar_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get meetings from Google Calendar"""
        if not self.service:
            logger.error("Not authenticated with Google Calendar")
            return []

        all_meetings = []

        try:
            # If no calendar IDs provided, get all calendars
            if not calendar_ids:
                calendar_list = self.service.calendarList().list().execute()
                calendar_ids = [item["id"] for item in calendar_list.get("items", [])]

            for calendar_id in calendar_ids:
                try:
                    events_result = (
                        self.service.events()
                        .list(
                            calendarId=calendar_id,
                            timeMin=start_date.isoformat() + "Z",
                            timeMax=end_date.isoformat() + "Z",
                            maxResults=1000,
                            singleEvents=True,
                            orderBy="startTime",
                        )
                        .execute()
                    )

                    events = events_result.get("items", [])

                    for event in events:
                        meeting_data = self._process_event(event, calendar_id)
                        if meeting_data:
                            all_meetings.append(meeting_data)

                except HttpError as e:
                    logger.warning(f"Error accessing calendar {calendar_id}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error with calendar {calendar_id}: {e}")
                    continue

            logger.info(f"Retrieved {len(all_meetings)} meetings from Google Calendar")
            return all_meetings

        except Exception as e:
            logger.error(f"Error retrieving meetings: {e}")
            return []

    def _process_event(
        self, event: Dict[str, Any], calendar_id: str
    ) -> Optional[Dict[str, Any]]:
        """Process a single calendar event"""
        try:
            summary = event.get("summary", "")
            description = event.get("description", "")

            # Skip all-day events and events without summary
            if not summary or event.get("start", {}).get("date"):
                return None

            # Extract meeting details
            start_time = event.get("start", {}).get("dateTime", "")
            end_time = event.get("end", {}).get("dateTime", "")

            # Parse attendees
            attendees = []
            for attendee in event.get("attendees", []):
                attendee_info = {
                    "email": attendee.get("email", ""),
                    "name": attendee.get("displayName", ""),
                    "response_status": attendee.get("responseStatus", ""),
                }
                attendees.append(attendee_info)

            # Extract location
            location = event.get("location", "")

            # Extract meeting URL if available
            meeting_url = ""
            if "hangoutLink" in event:
                meeting_url = event["hangoutLink"]
            elif "conferenceData" in event:
                conference_data = event["conferenceData"]
                if "entryPoints" in conference_data:
                    for entry_point in conference_data["entryPoints"]:
                        if entry_point.get("entryPointType") == "video":
                            meeting_url = entry_point.get("uri", "")
                            break

            return {
                "id": event.get("id", ""),
                "summary": summary,
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
                "location": location,
                "attendees": attendees,
                "meeting_url": meeting_url,
                "calendar_id": calendar_id,
                "created": event.get("created", ""),
                "updated": event.get("updated", ""),
                "status": event.get("status", ""),
                "html_link": event.get("htmlLink", ""),
            }

        except Exception as e:
            logger.warning(f"Error processing event: {e}")
            return None

    def get_calendar_list(self) -> List[Dict[str, Any]]:
        """Get list of available calendars"""
        if not self.service:
            logger.error("Not authenticated with Google Calendar")
            return []

        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = []

            for item in calendar_list.get("items", []):
                calendar_info = {
                    "id": item.get("id", ""),
                    "summary": item.get("summary", ""),
                    "description": item.get("description", ""),
                    "primary": item.get("primary", False),
                    "access_role": item.get("accessRole", ""),
                    "time_zone": item.get("timeZone", ""),
                    "selected": item.get("selected", True),
                }
                calendars.append(calendar_info)

            return calendars

        except Exception as e:
            logger.error(f"Error getting calendar list: {e}")
            return []

    def test_connection(self) -> bool:
        """Test the connection to Google Calendar"""
        try:
            if not self.authenticate():
                return False

            # Try to get calendar list
            calendars = self.get_calendar_list()
            if calendars:
                logger.info(
                    f"Successfully connected to Google Calendar. Found {len(calendars)} calendars."
                )
                return True
            else:
                logger.warning("Connected to Google Calendar but no calendars found.")
                return False

        except Exception as e:
            logger.error(f"Error testing Google Calendar connection: {e}")
            return False


def main():
    """Test the Google Calendar integration"""
    logging.basicConfig(level=logging.INFO)

    calendar = GoogleCalendarIntegration()

    if calendar.test_connection():
        print("✅ Google Calendar integration working!")

        # Test getting recent meetings
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        meetings = calendar.get_meetings(start_date, end_date)
        print(f"📅 Found {len(meetings)} meetings in the last 7 days")

        if meetings:
            print("\nRecent meetings:")
            for meeting in meetings[:5]:  # Show first 5
                print(f"  - {meeting['summary']} ({meeting['start_time']})")
    else:
        print("❌ Google Calendar integration failed")
        print("Please check your credentials and try again")


if __name__ == "__main__":
    main()
