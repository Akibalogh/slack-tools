# Slack Tools - Sales Commission Calculator

A comprehensive tool for analyzing Slack conversations and calculating sales commission splits based on deal stage participation, in-person meeting contributions, and strategic relationship context.

## Features

- **Multi-Platform Data Analysis**: Analyzes both Slack channels ending with '-bitsafe' AND Telegram group conversations for comprehensive sales tracking
- **Telegram Integration**: **NEW!** Processes Telegram HTML export data to capture conversations not available in Slack
- **Commission Calculation**: Calculates commission splits based on deal stage participation, message activity, and **in-person meeting contributions**
- **Stage Detection**: Identifies deal stages using keyword matching and confidence scoring across both Slack and Telegram
- **Google Calendar Integration**: Incorporates in-person meeting data from Google Calendar to provide complete sales activity tracking
- **Strategic Context Analysis**: Recognizes the difference between tactical execution and strategic relationship building
- **Output Generation**: Creates detailed commission reports, justifications, and rationale files
- **25% Rounding**: Ensures commission percentages are rounded to nearest 25% and sum to 100%

## Important Note: Strategic vs. Tactical Recognition

The system now includes **Google Calendar integration** and **strategic context analysis** to capture the complete picture of sales activities:

### Calendar Integration Features

- **Automatic Meeting Detection**: Searches for meetings with company names and key people
- **Duration Weighting**: In-person meetings receive 2x weight compared to Slack messages
- **Team Participation Tracking**: Identifies which team members attended each meeting
- **Comprehensive Coverage**: Includes meetings from the past 180 days

### Meeting Leadership Rules

**NEW!** When both Aki and Addie are present in a meeting, **Aki is considered the driver** and receives primary credit:

- **Dual Attendance**: If both Aki and Addie attend the same meeting, Aki receives driving credit
- **Leadership Recognition**: Aki's strategic role and relationship ownership is acknowledged
- **Credit Distribution**: Aki gets primary meeting credit, Addie gets supporting credit

This rule ensures that strategic leadership and relationship ownership are properly recognized in commission calculations.

## Telegram Integration

**NEW!** The system now integrates Telegram conversation data alongside Slack data for comprehensive sales activity tracking:

### How It Works

1. **HTML Export Processing**: Parses Telegram HTML export files from `data/telegram/DataExport_2025-08-19/`
2. **Company Matching**: Maps 82 HubSpot CRM companies to their corresponding Telegram groups
3. **Message Analysis**: Processes Telegram messages for stage detection using the same keywords as Slack
4. **Team Member Mapping**: Identifies internal team members by both Slack IDs and display names
5. **Combined Analysis**: Integrates Telegram data with Slack and Calendar data for complete commission calculation

### Telegram Group Patterns

Most Telegram groups follow these naming patterns:
- `Company <> BitSafe (iBTC, CBTC)` - Most common
- `Company <> iBTC` - Second most common  
- `Company / BitSafe` - Alternative format
- `Company - Other` - Rare cases

### Data Coverage

- **Total HubSpot Companies**: 235
- **Telegram Matches**: 82 companies (34.9% match rate)
- **Key Companies**: P2P, ChainSafe, Copper, 7Ridge, Hashkey Cloud, Launchnodes, Republic, Gemini, BitGo, and many more

### Impact on Commission Analysis

Telegram integration provides a more complete picture of sales activities, especially for companies where:
- Slack channels were deleted or not created
- Primary communication happened via Telegram
- International customers preferred Telegram over Slack

**Example**: P2P analysis shows Aki with 77 Telegram messages vs minimal Slack activity, providing a much more accurate commission split.

### Strategic Context Analysis

Recent analysis of Addie's comprehensive Slack export revealed important insights:

- **Addie's Role**: Excellent tactical execution, pipeline management, and individual deal coordination
- **Aki's Role**: Strategic relationships, broader company engagement, and in-person meeting ownership
- **Current System Gap**: Over-weights Slack activity vs. relationship depth and strategic involvement

**Examples:**
- **Black Manta**: Aki added Finn to `cbtc-holders` channel (strategic relationship) + in-person meetings
- **Vigil Markets**: Aki met with Soumya in person + broader strategic engagement beyond bitsafe

This analysis shows the need for better recognition of strategic vs. tactical contributions in commission calculations.

## Output Files

- `deal_splits.csv`: Commission percentages for each deal
- `person_rollup.csv`: Total commission percentages per person
- `deal_rationale.csv`: **NEW!** Includes calendar meeting information, stage breakdown, and strategic context
- `justifications/`: Detailed markdown files for each deal with calendar data and strategic insights 