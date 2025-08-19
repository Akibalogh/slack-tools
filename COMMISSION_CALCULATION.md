# Commission Calculation Documentation

## Overview

The commission calculation system analyzes Slack conversations and Google Calendar data to determine fair commission splits based on actual sales activity and in-person meeting contributions.

## Recent Improvements

### Addie Slack Export Analysis (NEW!)

Analysis of Addie's comprehensive Slack export revealed important insights about commission calculation accuracy and the need for broader context beyond individual deal channels.

#### Key Findings

1. **Strategic vs. Tactical Role Recognition**
   - **Addie's Role**: Excellent tactical execution, pipeline management, document handling, and individual deal coordination
   - **Aki's Role**: Strategic relationships, broader company engagement, and in-person meeting ownership
   - **Current System Gap**: Over-weights Slack activity vs. relationship depth and strategic involvement

2. **Cross-Channel Activity Missing**
   - **Black Manta**: Aki added Finn to `cbtc-holders` channel, showing broader relationship management
   - **Vigil Markets**: Soumya was added to `gsf-outreach` channel, indicating strategic engagement beyond bitsafe
   - **Impact**: Current analysis only considers bitsafe channels, missing strategic relationship context

3. **Business Development Pipeline Context**
   - Addie manages comprehensive pipeline of 15+ companies with detailed status tracking
   - Includes companies like Chain Experts, Barg Systems, Vigil Markets, Tenkai, Cense, Modulo Finance
   - Shows Addie's role as strategic pipeline manager, not just individual deal closer

#### Commission Analysis Implications

**Black Manta Deal:**
- **Current Analysis**: Addie 75%, Aki 25% (based only on bitsafe channel)
- **Enhanced Context**: Aki had direct relationship with Finn, broader company engagement
- **Expected Impact**: Aki's percentage should increase to 40-50% due to strategic relationship ownership

**Vigil Markets Deal:**
- **Current Analysis**: Addie 75%, Aki 25% (based only on bitsafe channel)
- **Enhanced Context**: Aki met with Soumya in person, had broader strategic involvement
- **Expected Impact**: More balanced split reflecting strategic vs. tactical roles

#### Recommendations for Enhanced Analysis

1. **Include Cross-Channel Activity**: Consider activity across multiple channels for the same company
2. **Weight Strategic vs. Tactical**: Give more weight to relationship building vs. document management
3. **Calendar Integration Enhancement**: Improve meeting detection for key people and companies
4. **Relationship Depth Scoring**: Consider the depth of relationships (adding key people to channels)

### Google Calendar Integration (NEW!)

The system now incorporates **in-person meeting data** from Google Calendar to provide a complete picture of sales activities that may not be captured in Slack.

#### How It Works

1. **Meeting Detection**: For each deal, the system searches for:
   - Meetings with the company name
   - Meetings with key people from the company (e.g., "Finn" for Black Manta, "Soumya" for Vigil Markets)

2. **Duration Weighting**: In-person meetings receive **2x weight** compared to Slack messages, reflecting their higher value in the sales process

3. **Team Participation**: Identifies which team members attended each meeting and assigns credit accordingly

4. **Comprehensive Coverage**: Searches meetings from the past 180 days to capture all relevant interactions

#### Example: Black Manta Deal

- **Slack Activity**: Aki and Addie both active in channel
- **Calendar Meetings**: 
  - Multiple meetings with Oscar (Finn's colleague) - Aki and Addie both present
  - Total meeting time: 9 meetings × 30-60 minutes each
- **Result**: Calendar contributions significantly boost both Aki and Addie's commission percentages

#### Example: Vigil Markets Deal

- **Slack Activity**: Addie active in channel
- **Calendar Meetings**:
  - "Soumya Basu and Addie Tackman" (30 min) - Aki and Addie present
  - "Soumya / Aki" (60 min) - Aki only present
- **Result**: Aki's in-person meeting with Soumya gives him substantial additional credit

### Enhanced Contestation Logic

The system now provides more aggressive contestation classification:

- **CLEAR OWNERSHIP**: ≥60% commission OR ≥40% with ≤2 participants
- **HIGH CONTESTATION**: ≥3 participants OR <40% max with ≥2 participants  
- **MODERATE CONTESTATION**: All other cases

### Stage-by-Stage Breakdown

The `deal_rationale.csv` now includes detailed stage breakdown showing who handled each sales stage:

- Sourcing/Intro
- Discovery/Qualification
- Solution Presentation
- Objection Handling
- Technical Discussion
- Pricing/Terms
- Contract/Legal
- Scheduling/Coordination
- Closing/Onboarding

## Core Calculation Logic

### 1. Stage Detection & Confidence Scoring

Each Slack message is analyzed for keywords associated with different deal stages:

```python
confidence = min(1.0, 0.3 + (matches * 0.4))
```

Where:
- `0.3` = Base confidence for any message
- `matches` = Number of keyword matches found
- `0.4` = Multiplier per keyword match

### 2. Commission Calculation

For each participant, the system calculates:

```python
total_contribution = (
    stage_confidence * stage_weight +
    message_count * 0.1 +
    calendar_meetings * 2.0 +  # NEW: Calendar weighting
    time_bonus
)
```

### 3. 25% Rounding & Normalization

1. **Initial Calculation**: Raw percentages based on contributions
2. **25% Rounding**: Round to nearest 25% (0%, 25%, 50%, 75%, 100%)
3. **Protection Rule**: If participant had >5% but got rounded to 0%, give them 25%
4. **Normalization**: Ensure total equals 100%

## Deal Stages & Weights

| Stage | Weight | Keywords |
|-------|--------|----------|
| **sourcing_intro** | 8% | intro, connect, loop in, reached out, waitlist, referral |
| **discovery_qual** | 12% | questions, requirements, use case, needs, challenge, timeline |
| **solution_presentation** | 15% | credential, rewards, CC, CBTC, overview, explain, how it works |
| **objection_handling** | 18% | concern, worried, hesitant, not sure, doubt, question, issue |
| **technical_discussion** | 12% | API, integration, technical, architecture, implementation |
| **pricing_terms** | 15% | cost, payment, billing, subscription, pricing, fee, rate |
| **contract_legal** | 8% | MSA, contract, agreement, terms, legal, docusign |
| **scheduling_coordination** | 5% | Calendly, schedule, meeting, call, demo, follow up |
| **closing_onboarding** | 7% | signed, accept, onboard, credential issued, go live |

## Commission Rules

### Core Principles

- **Fair Distribution**: Based on actual contribution to deal success
- **Transparency**: Every commission allocation backed by specific data
- **Completeness**: Includes both digital (Slack) and in-person (Calendar) activities
- **Strategic Recognition**: Considers relationship depth and strategic involvement

### Specific Rules

1. **25% Rounding**: All percentages rounded to nearest 25%
2. **100% Total**: Commissions always sum to exactly 100%
3. **Calendar Weighting**: In-person meetings get 2x weight vs Slack messages
4. **Presence Floor**: Minimum 5% for any participant
5. **No Founder Cap**: Aki can earn full commission based on actual contribution
6. **Internal Team Only**: External prospects/clients excluded from calculations
7. **Strategic Weighting**: Relationship building and strategic involvement weighted higher than tactical execution

### Meeting Leadership Rules

**NEW!** When both Aki and Addie are present in a meeting, **Aki is considered the driver** and should receive primary credit:

- **Dual Attendance**: If both Aki and Addie attend the same meeting, Aki receives driving credit
- **Leadership Recognition**: Aki's strategic role and relationship ownership is acknowledged
- **Credit Distribution**: Aki gets primary meeting credit, Addie gets supporting credit
- **Business Context**: Reflects Aki's role as strategic relationship owner and meeting driver

**Example Scenarios:**
- **Black Manta**: Aki + Addie meetings → Aki drives, Addie supports
- **Vigil Markets**: Aki + Addie meetings → Aki drives, Addie supports
- **Solo Meetings**: Individual meetings receive full credit for the attendee

This rule ensures that strategic leadership and relationship ownership are properly recognized in commission calculations, even when multiple team members are present.

### Protection Mechanisms

- **Anti-Zero Rule**: Participants with >5% contribution cannot be rounded to 0%
- **Over-100% Handling**: If rounding causes total >100%, reduce highest participant by 25%
- **Graceful Degradation**: Calendar integration failures don't break Slack analysis

## Output Files

### 1. deal_splits.csv
Basic commission percentages per deal

### 2. person_rollup.csv  
Total commission percentages per person across all deals

### 3. deal_rationale.csv (Enhanced)
- Commission percentages (25% rounded)
- Contestation level and most likely owner
- **NEW: Calendar meeting summary**
- Stage-by-stage breakdown
- Detailed rationale

### 4. justifications/ (Enhanced)
Detailed markdown files per deal including:
- Commission breakdown
- **NEW: Calendar meeting details**
- Stage analysis
- Message references

## Technical Implementation

### Calendar Integration

The system uses the Google Calendar API to:

1. **Authenticate**: OAuth 2.0 flow for secure access
2. **Search**: Find meetings by company name and key people
3. **Process**: Extract duration, attendees, and meeting details
4. **Integrate**: Combine calendar data with Slack analysis

### Database Schema

The SQLite database stores:
- Slack messages and stage detections
- User information and participant mappings
- Conversation metadata and channel information

### Performance Considerations

- Calendar API calls are cached and rate-limited
- 180-day search window balances completeness with performance
- Graceful fallback if calendar integration fails

## Future Enhancements

### Planned Improvements

1. **Cross-Channel Analysis**: Include activity across multiple channels for same company
2. **Strategic Relationship Scoring**: Better recognition of relationship depth vs. tactical execution
3. **Meeting Outcome Tracking**: Classify meetings by success/failure
4. **Multi-Calendar Support**: Include team member calendars beyond Aki's
5. **Advanced Weighting**: Dynamic weights based on deal stage and meeting type

### Research Areas

- **AI-Powered Analysis**: Better message quality assessment
- **Deal Outcome Correlation**: Link activities to deal success rates
- **Predictive Modeling**: Estimate commission splits for new deals
- **Relationship Mapping**: Track strategic vs. tactical contributions across channels

## Troubleshooting

### Common Issues

1. **Calendar Authentication Failed**
   - Check `token.json` file exists and is valid
   - Verify Google Calendar API is enabled
   - Ensure OAuth credentials are correct

2. **No Meetings Found**
   - Verify company name mapping in calendar search
   - Check search window (default: 180 days)
   - Review key people configuration

3. **Integration Errors**
   - Check Python dependencies (`google-auth`, `google-auth-oauthlib`)
   - Verify calendar API quotas and limits
   - Review error logs for specific failure reasons

### Debug Mode

Enable detailed logging by setting log level to DEBUG in `repsplit.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- Calendar API calls and responses
- Meeting detection and processing
- Commission calculation steps
- Integration success/failure details
