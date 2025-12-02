#!/usr/bin/env python3
"""Search for Launchnodes meetings in personal calendars"""

from google_calendar_integration import GoogleCalendarIntegration


def main():
    calendar = GoogleCalendarIntegration()

    if not calendar.authenticate():
        print("Failed to authenticate")
        return

    print("✅ Authenticated with Google Calendar")

    # Focus on individual team member calendars
    personal_calendars = [
        "aki@dlc.link",
        "addie@dlc.link",
        "mayank@dlc.link",
        "amy@dlc.link",
        "kadeem@dlc.link",
        "anna@dlc.link",
    ]

    print("\n🔍 Searching personal calendars for Launchnodes meetings...")

    all_meetings = []

    for calendar_id in personal_calendars:
        try:
            print(f"\n📅 Checking {calendar_id}...")

            # Search for Launchnodes related events
            meetings = calendar.search_meetings_for_company(
                "Launchnodes", days_back=180
            )
            if meetings:
                print(f"  Found {len(meetings)} Launchnodes meetings:")
                for meeting in meetings:
                    print(
                        f"    - {meeting['title']} ({meeting['start']}) - {meeting['duration_minutes']} min"
                    )
                    all_meetings.extend(meetings)

            # Also search for variations
            variations = [
                "LaunchNodes",
                "launchnodes",
                "Launch Node",
                "Jaydeep",
                "BitSafe",
            ]
            for var in variations:
                var_meetings = calendar.search_meetings_for_company(var, days_back=180)
                if var_meetings:
                    print(f"  Found {len(var_meetings)} meetings with '{var}':")
                    for meeting in var_meetings:
                        print(
                            f"    - {meeting['title']} ({meeting['start']}) - {meeting['duration_minutes']} min"
                        )
                        all_meetings.extend(var_meetings)

        except Exception as e:
            print(f"  Error searching {calendar_id}: {e}")

    print(f"\n📊 Summary:")
    print(f"  Total meetings found: {len(all_meetings)}")

    if all_meetings:
        print(
            f"  Total meeting time: {sum(m['duration_minutes'] for m in all_meetings)} minutes"
        )

        # Group by attendee
        attendees = {}
        for meeting in all_meetings:
            for attendee in meeting["attendees"]:
                if attendee:
                    if attendee not in attendees:
                        attendees[attendee] = 0
                    attendees[attendee] += meeting["duration_minutes"]

        print(f"\n👥 Attendee Summary:")
        for attendee, minutes in sorted(
            attendees.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {attendee}: {minutes} minutes")


if __name__ == "__main__":
    main()
