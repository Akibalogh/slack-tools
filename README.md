# Slack Tools - Sales Commission Calculator

A comprehensive tool for analyzing Slack conversations and calculating sales commission splits based on deal stage participation, in-person meeting contributions, and strategic relationship context.

## Features

- **Slack Data Analysis**: Analyzes private Slack channels ending with '-bitsafe' for sales deal tracking
- **Commission Calculation**: Calculates commission splits based on deal stage participation, message activity, and **in-person meeting contributions**
- **Stage Detection**: Identifies deal stages using keyword matching and confidence scoring
- **Google Calendar Integration**: **NEW!** Incorporates in-person meeting data from Google Calendar to provide complete sales activity tracking
- **Strategic Context Analysis**: **NEW!** Recognizes the difference between tactical execution and strategic relationship building
- **Output Generation**: Creates detailed commission reports, justifications, and rationale files
- **25% Rounding**: Ensures commission percentages are rounded to nearest 25% and sum to 100%

## Important Note: Strategic vs. Tactical Recognition

The system now includes **Google Calendar integration** and **strategic context analysis** to capture the complete picture of sales activities:

### Calendar Integration Features

- **Automatic Meeting Detection**: Searches for meetings with company names and key people
- **Duration Weighting**: In-person meetings receive 2x weight compared to Slack messages
- **Team Participation Tracking**: Identifies which team members attended each meeting
- **Comprehensive Coverage**: Includes meetings from the past 180 days

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