# Commission Calculation System Documentation

## Overview

The RepSplit commission calculation system analyzes Slack conversations to determine fair commission splits based on sales team participation in different deal stages. The system uses message content analysis, stage detection, and business rules to calculate commission percentages.

## Core Components

### 1. Deal Stage Detection
The system identifies deal stages by analyzing message content using keyword patterns:

| Stage | Weight | Keywords | Purpose |
|-------|--------|----------|---------|
| **Sourcing Intro** | 8.0% | intro, connect, loop in, reached out, waitlist, referral | Initial contact and introduction |
| **Discovery Qual** | 12.0% | questions, requirements, use case, needs, challenge, timeline | Understanding customer needs |
| **Solution Presentation** | 32.0% | credential, rewards, CC, CBTC, overview, explain, how it works | Presenting the solution |
| **Technical Discussion** | 5.0% | API, integration, technical, architecture, implementation, script | Technical details and integration |
| **Pricing Terms** | 8.0% | $6000, cost, payment, billing, subscription, pricing | Pricing discussions |
| **Contract Legal** | 15.0% | MSA, contract, agreement, terms, legal, docusign, dropbox sign | Legal and contract work |
| **Scheduling Coordination** | 8.0% | Calendly, schedule, meeting, call, demo, follow up | Meeting coordination |
| **Closing Onboarding** | 12.0% | signed, accept, onboard, credential issued, go live, activate | Deal closure and onboarding |

**Total Stage Weight: 100%**

### 2. Message Analysis Process

1. **Message Ingestion**: All messages from `-bitsafe` channels are loaded into SQLite database
2. **Stage Detection**: Each message is analyzed for stage keywords using regex patterns
3. **Confidence Scoring**: Messages are scored based on keyword matches and context
4. **Participant Attribution**: Each message is attributed to its author
5. **Stage Mapping**: Messages are grouped by detected stage and participant

### 3. Commission Calculation Logic

#### Step 1: Raw Contribution Calculation
```
For each participant in each stage:
- Count messages by participant
- Apply confidence scores to messages
- Calculate raw contribution per stage
```

#### Step 2: Diminishing Returns
```
For repeated contributions in the same stage:
- First contribution: 100% weight
- Second contribution: 50% weight (configurable)
- Third+ contribution: 25% weight (configurable)
```

#### Step 3: Stage Weight Application
```
For each stage:
- Apply stage weight (e.g., Solution Presentation = 32%)
- Distribute weight among participants proportionally
- Example: If Aki has 60% of messages in Solution Presentation
  → Aki gets: 32% × 60% = 19.2% commission
```

#### Step 4: Business Rules Application

**Founder Cap (Aki)**
- Default cap: 30% of total commission
- Exception: If Aki participates in negotiation/closing stages, cap is lifted
- Excess commission is redistributed to other participants

**Presence Floor**
- Minimum commission: 5% (configurable)
- Participants below threshold get 0% instead of small percentages

**Minimum Participation Threshold**
- Participants must meet minimum activity level to qualify
- Prevents very small contributions from receiving commission

#### Step 5: Normalization
```
- Sum all participant commissions
- If total ≠ 100%, normalize to 100%
- If total = 0%, distribute equally among participants
```

#### Step 6: 25% Rounding (New Feature)
```
Final percentages are rounded to nearest 25%:
- 0-12.5% → 0%
- 12.6-37.5% → 25%
- 37.6-62.5% → 50%
- 62.6-87.5% → 75%
- 87.6%+ → 100%
```

## Example Calculation

### Scenario: 3-Participant Deal

**Raw Message Counts by Stage:**
- **Sourcing Intro (8% weight)**: Aki: 2, Addie: 1
- **Discovery Qual (12% weight)**: Aki: 3, Addie: 2, Amy: 1
- **Solution Presentation (32% weight)**: Aki: 5, Addie: 3, Amy: 2

**Step-by-Step Calculation:**

1. **Sourcing Intro (8% total)**
   - Aki: 2/3 = 66.7% → 8% × 66.7% = 5.33%
   - Addie: 1/3 = 33.3% → 8% × 33.3% = 2.67%

2. **Discovery Qual (12% total)**
   - Aki: 3/6 = 50% → 12% × 50% = 6%
   - Addie: 2/6 = 33.3% → 12% × 33.3% = 4%
   - Amy: 1/6 = 16.7% → 12% × 16.7% = 2%

3. **Solution Presentation (32% total)**
   - Aki: 5/10 = 50% → 32% × 50% = 16%
   - Addie: 3/10 = 30% → 32% × 30% = 9.6%
   - Amy: 2/10 = 20% → 32% × 20% = 6.4%

4. **Raw Totals:**
   - Aki: 5.33% + 6% + 16% = 27.33%
   - Addie: 2.67% + 4% + 9.6% = 16.27%
   - Amy: 2% + 6.4% = 8.4%

5. **Apply Business Rules:**
   - Founder cap: Aki at 27.33% (under 30% cap) → No change
   - Presence floor: All above 5% → No change

6. **Normalize to 100%:**
   - Total: 27.33% + 16.27% + 8.4% = 52%
   - Normalization factor: 100% / 52% = 1.923
   - Aki: 27.33% × 1.923 = 52.6%
   - Addie: 16.27% × 1.923 = 31.3%
   - Amy: 8.4% × 1.923 = 16.2%

7. **Apply 25% Rounding:**
   - Aki: 52.6% → 50%
   - Addie: 31.3% → 25%
   - Amy: 16.2% → 25%

**Final Result: Aki: 50%, Addie: 25%, Amy: 25%**

## Configuration Options

### Stage Weights
Edit `config.json` to adjust stage importance:
```json
{
  "stages": [
    {"name": "sourcing_intro", "weight": 8.0, "keywords": [...]},
    {"name": "discovery_qual", "weight": 12.0, "keywords": [...]}
  ]
}
```

### Business Rules
```json
{
  "commission_rules": {
    "founder_cap": 0.30,
    "presence_floor": 0.05,
    "min_participation": 0.02,
    "diminishing_returns": 0.5
  }
}
```

### Participant Configuration
```json
{
  "participants": [
    {
      "name": "Aki",
      "slack_id": "U123456",
      "display_name": "Aki Balogh",
      "email": "aki@company.com",
      "role": "Founder"
    }
  ]
}
```

## Output Files

### 1. deal_splits.csv
Commission percentages per deal/channel for each participant.

### 2. person_rollup.csv
Total commission percentages per person across all deals.

### 3. justifications/
Detailed markdown files explaining commission splits for each deal, including:
- Stage-by-stage analysis
- Message references
- Confidence scores
- Final commission allocation

## Edge Cases & Considerations

### 1. Equal Participation
If all participants have identical contribution patterns, they receive equal splits.

### 2. Single Participant
If only one person participates, they receive 100% commission.

### 3. No Activity
If no sales activity is detected, commission is split equally among channel members.

### 4. Rounding Discrepancies
25% rounding may result in total percentages ≠ 100%. This is intentional for simplicity.

### 5. Founder Cap Logic
The founder cap only applies when Aki is not involved in later-stage activities, ensuring fair compensation for critical deal stages.

## Troubleshooting

### Common Issues

1. **All participants getting 0%**: Check stage detection keywords and message content
2. **Uneven distribution**: Verify diminishing returns and business rule settings
3. **Missing participants**: Ensure Slack user IDs are correctly mapped in config
4. **Low confidence scores**: Review keyword patterns and message analysis logic

### Debug Mode
Enable detailed logging in `repsplit.py` to see:
- Stage detection results
- Confidence scores
- Business rule applications
- Commission calculation steps

## Future Enhancements

1. **Dynamic Stage Weights**: Adjust weights based on deal size or complexity
2. **Time-based Decay**: Reduce weight of older activities
3. **Role-based Multipliers**: Different weights for different team roles
4. **Deal Outcome Integration**: Adjust commissions based on deal success/failure
5. **Custom Rounding Rules**: Configurable rounding thresholds beyond 25%

---

*This documentation covers the RepSplit commission calculation system as of August 2025. For questions or updates, refer to the code comments and configuration files.*
