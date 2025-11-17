# Company Mapping and Entity Resolution

## Overview

The company mapping system resolves different company name variants, subsidiaries, and related entities to ensure accurate commission tracking and data analysis. This system handles the complexity of modern business structures where companies may have multiple legal entities, trading names, and operational divisions.

## Company Entity Types

### Base Company
**Definition**: The primary legal entity or main business unit
**Characteristics**:
- Official legal name
- Primary business registration
- Main headquarters location
- Primary business operations

**Examples**:
- "Acme Corporation"
- "Tech Solutions Inc."
- "Global Services Ltd."

### Subsidiary Companies
**Definition**: Legal entities owned or controlled by the base company
**Characteristics**:
- Separate legal entity
- Owned by base company
- May have different business focus
- Shared management or resources

**Examples**:
- "Acme Corporation" → "Acme Technologies LLC"
- "Tech Solutions Inc." → "Tech Solutions Europe Ltd."
- "Global Services Ltd." → "Global Services Asia Pte Ltd."

### Trading Names
**Definition**: Alternative names used for business operations
**Characteristics**:
- Not legal entities
- Used for marketing or branding
- May be more recognizable than legal name
- Same business operations as base company

**Examples**:
- "Acme Corporation" → "AcmeTech"
- "Tech Solutions Inc." → "TechSol"
- "Global Services Ltd." → "GlobalServ"

### Division Names
**Definition**: Internal divisions or business units within a company
**Characteristics**:
- Not separate legal entities
- Different business focus or market
- May have separate management
- Shared parent company resources

**Examples**:
- "Acme Corporation" → "Acme Healthcare Division"
- "Tech Solutions Inc." → "Tech Solutions Cloud Services"
- "Global Services Ltd." → "Global Services Consulting"

### Minter Variants
**Definition**: Specialized variants for blockchain or cryptocurrency operations
**Characteristics**:
- Related to blockchain operations
- May be separate legal entities
- Often have "minter" in the name
- Connected to base company's blockchain activities

**Examples**:
- "AllNodes" → "AllNodes Minter"
- "Blockchain Corp" → "Blockchain Corp Minter"
- "Crypto Solutions" → "Crypto Solutions Minter"

### Mainnet Variants
**Definition**: Variants related to mainnet blockchain operations
**Characteristics**:
- Blockchain network operations
- May be separate legal entities
- Often have "mainnet" in the name
- Connected to base company's blockchain infrastructure

**Examples**:
- "AllNodes" → "AllNodes Mainnet"
- "Blockchain Corp" → "Blockchain Corp Mainnet"
- "Crypto Solutions" → "Crypto Solutions Mainnet"

### Validator Variants
**Definition**: Variants related to blockchain validation operations
**Characteristics**:
- Blockchain validation services
- May be separate legal entities
- Often have "validator" in the name
- Connected to base company's validation activities

**Examples**:
- "AllNodes" → "AllNodes Validator"
- "Blockchain Corp" → "Blockchain Corp Validator"
- "Crypto Solutions" → "Crypto Solutions Validator"

## Company Mapping Rules

### Primary Mapping Rules
1. **Exact Match**: Direct name match with base company
2. **Subsidiary Match**: Subsidiary company maps to parent
3. **Trading Name Match**: Trading name maps to legal entity
4. **Division Match**: Division maps to parent company
5. **Variant Match**: Specialized variants map to base company

### Mapping Priority
1. **Legal Entity**: Highest priority for legal accuracy
2. **Business Unit**: Medium priority for operational accuracy
3. **Trading Name**: Lower priority for marketing accuracy
4. **Variant Name**: Lowest priority for specialized accuracy

### Mapping Validation
1. **Data Source Confirmation**: Multiple sources confirm mapping
2. **Business Logic Check**: Mapping makes business sense
3. **Historical Validation**: Previous mappings support current mapping
4. **Manual Review**: Complex mappings require human review

## Data Source Integration

### Slack Data Mapping
- **Channel Names**: Company names in Slack channel names
- **User Profiles**: Company affiliations in user profiles
- **Message Content**: Company mentions in messages
- **File Names**: Company names in file names

### Telegram Data Mapping
- **Chat Names**: Company names in chat titles
- **User Names**: Company affiliations in usernames
- **Message Content**: Company mentions in messages
- **Group Descriptions**: Company information in group descriptions

### Calendar Data Mapping
- **Meeting Titles**: Company names in meeting titles
- **Attendee Names**: Company affiliations in attendee lists
- **Location Names**: Company names in meeting locations
- **Description Fields**: Company mentions in meeting descriptions

### HubSpot Data Mapping
- **Company Records**: Official company records in CRM
- **Contact Records**: Company affiliations in contact records
- **Deal Records**: Company associations in deal records
- **Activity Records**: Company mentions in activity logs

## Company Variant Detection

### Name Pattern Recognition
- **Suffix Patterns**: "Inc.", "LLC", "Ltd.", "Corp."
- **Prefix Patterns**: "The", "A", "An"
- **Abbreviation Patterns**: "Tech", "Solutions", "Services"
- **Specialized Patterns**: "Minter", "Mainnet", "Validator"

### Fuzzy Matching
- **Levenshtein Distance**: Character-level similarity
- **Soundex Matching**: Phonetic similarity
- **N-gram Matching**: Substring similarity
- **Semantic Matching**: Meaning-based similarity

### Context-Based Matching
- **Industry Context**: Similar companies in same industry
- **Geographic Context**: Companies in same region
- **Size Context**: Companies of similar size
- **Technology Context**: Companies using similar technologies

## Commission Impact of Company Mapping

### Unified Commission Tracking
- **Cross-Entity Activities**: Activities across variants count toward same deal
- **Unified Deal Value**: Total deal value across all entities
- **Shared Commission Pool**: Commission shared across all participants
- **Consolidated Reporting**: Single report for all company variants

### Commission Splitting Rules
1. **Base Company**: Primary commission recipient
2. **Subsidiary Companies**: Proportional commission based on involvement
3. **Trading Names**: Commission follows base company
4. **Division Names**: Commission follows parent company
5. **Variant Names**: Commission follows base company

### Activity Aggregation
- **Slack Activities**: All Slack activities across variants
- **Telegram Activities**: All Telegram activities across variants
- **Calendar Activities**: All calendar activities across variants
- **HubSpot Activities**: All HubSpot activities across variants

## Data Quality and Validation

### Mapping Accuracy Metrics
- **Exact Match Rate**: Percentage of exact name matches
- **Fuzzy Match Rate**: Percentage of fuzzy name matches
- **Manual Review Rate**: Percentage requiring manual review
- **Error Rate**: Percentage of incorrect mappings

### Data Quality Checks
1. **Duplicate Detection**: Identify duplicate company records
2. **Inconsistency Detection**: Find conflicting company information
3. **Completeness Check**: Ensure all required fields are populated
4. **Validation Rules**: Apply business rules to validate mappings

### Error Handling
- **Mapping Errors**: Incorrect company mappings
- **Data Inconsistencies**: Conflicting company information
- **Missing Mappings**: Companies without proper mappings
- **Ambiguous Mappings**: Multiple possible mappings

## Company Mapping Examples

### Example 1: Simple Base Company
**Base Company**: "Acme Corporation"
**Variants**:
- "Acme Corp"
- "Acme Technologies"
- "AcmeTech"
- "Acme Healthcare Division"

**Mapping**: All variants map to "Acme Corporation"
**Commission**: All activities count toward "Acme Corporation" deal

### Example 2: Complex Subsidiary Structure
**Base Company**: "Global Services Ltd."
**Subsidiaries**:
- "Global Services Europe Ltd."
- "Global Services Asia Pte Ltd."
- "Global Services Americas Inc."

**Mapping**: All subsidiaries map to "Global Services Ltd."
**Commission**: All activities count toward "Global Services Ltd." deal

### Example 3: Blockchain Company with Variants
**Base Company**: "AllNodes"
**Variants**:
- "AllNodes Minter"
- "AllNodes Mainnet"
- "AllNodes Validator"
- "AllNodes Technologies"

**Mapping**: All variants map to "AllNodes"
**Commission**: All activities count toward "AllNodes" deal

### Example 4: Trading Name Company
**Base Company**: "Tech Solutions Inc."
**Trading Names**:
- "TechSol"
- "Tech Solutions"
- "TSI"
- "Tech Solutions Cloud"

**Mapping**: All trading names map to "Tech Solutions Inc."
**Commission**: All activities count toward "Tech Solutions Inc." deal

## Integration with NotebookLM

This documentation enables NotebookLM to:
- Understand company entity relationships and mapping rules
- Identify the correct base company for any company variant
- Analyze commission data across all company entities
- Provide insights on company relationship patterns
- Answer questions about company mapping and entity resolution
- Suggest improvements to company mapping accuracy
- Understand the business impact of company mapping decisions
