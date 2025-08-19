# Changelog

All notable changes to the Slack Tools project will be documented in this file.

## [Unreleased]

### Added
- **Meeting Leadership Rules**: NEW! When both Aki and Addie are present in a meeting, Aki is considered the driver and receives primary credit
  - Dual attendance meetings give Aki driving credit, Addie supporting credit
  - Reflects Aki's strategic role and relationship ownership
  - Ensures proper recognition of meeting leadership in commission calculations
- **Addie Slack Export Analysis**: NEW! Comprehensive analysis of Addie's Slack export revealed critical insights about commission calculation accuracy
  - Strategic vs. tactical role recognition (Addie: tactical execution, Aki: strategic relationships)
  - Cross-channel activity missing from current analysis (e.g., Aki adding Finn to cbtc-holders, Soumya to gsf-outreach)
  - Business development pipeline context showing Addie's role as strategic pipeline manager
  - Recommendations for enhanced analysis including cross-channel activity and strategic weighting
- **Google Calendar Integration**: NEW! The system now incorporates in-person meeting data from Google Calendar to provide complete sales activity tracking
  - Automatic meeting detection for company names and key people
  - Duration-based weighting (2x weight for in-person vs Slack messages)
  - Team participation tracking and credit assignment
  - 180-day search window for comprehensive coverage
  - Graceful fallback if calendar integration fails
- **Enhanced Output Files**: 
  - `deal_rationale.csv` now includes calendar meeting summaries
  - Justification files show detailed meeting information
  - Calendar contributions visible in all commission reports

### Changed
- **Commission Calculation**: In-person meetings now receive 2x weight compared to Slack messages
- **Meeting Detection**: Improved search logic to find meetings by both company name and key people (e.g., "Finn" for Black Manta, "Soumya" for Vigil Markets)
- **Commission Rules**: Added strategic weighting to recognize relationship depth vs. tactical execution

### Technical
- **Calendar API Integration**: Added Google Calendar API authentication and search capabilities
- **Performance**: Calendar API calls are cached and rate-limited for optimal performance
- **Error Handling**: Robust error handling ensures calendar failures don't break Slack analysis

## [2025-08-19] - Commission System Overhaul

### Added
- **25% Commission Rounding**: All commission percentages now rounded to nearest 25% (0%, 25%, 50%, 75%, 100%)
- **Enhanced Contestation Logic**: More aggressive identification of clear ownership vs. contested deals
- **Stage-by-Stage Breakdown**: Detailed breakdown showing who handled each sales stage
- **Enhanced Rationale Generation**: Comprehensive explanation of commission splits with stage participation details

### Changed
- **Commission Calculation**: Improved logic to ensure totals always sum to 100%
- **Stage Weights**: Adjusted weights based on business importance and sales process flow
- **User ID Mapping**: Fixed incorrect mapping between Slack IDs and participant names

### Fixed
- **Commission Totals**: Resolved issue where commission percentages didn't sum to 100%
- **External User Filtering**: Corrected logic to exclude external prospects/clients from calculations
- **Founder Cap Removal**: Eliminated artificial 30% cap on Aki's commission
- **Rounding Protection**: Added rule to prevent legitimate contributions from being rounded down to 0%

## [2025-08-18] - Message Engagement Quality Discovery

### Added
- **Message Quality Analysis**: Recognition that not all messages are equal in value
- **Engagement Scoring**: Distinction between high-value (response-generating) and low-value (ignored) messages

### Changed
- **Commission Logic**: Updated to consider message engagement quality
- **Documentation**: Added comprehensive notes about message engagement quality impact

### Technical
- **AI-Powered Assessment**: Implemented and then removed AI-powered message quality filtering
- **Confidence Calculation**: Refined confidence scoring to better reflect actual sales activity

## [2025-08-17] - External User Filtering

### Added
- **External User Detection**: Logic to identify and exclude external prospects/clients
- **Internal Team Filtering**: Messages and stage detections filtered by internal team only

### Changed
- **Commission Calculation**: Only internal team members eligible for commission
- **Stage Attribution**: External users cannot be assigned deal stages or commission credit

### Fixed
- **User Attribution**: Resolved issue where external users were receiving commission credit
- **Data Cleanup**: Removed external user data from commission calculations

## [2025-08-16] - Contestation Logic Refinement

### Added
- **Contestation Levels**: CLEAR OWNERSHIP, HIGH CONTESTATION, MODERATE CONTESTATION
- **Most Likely Owner**: Primary deal owner recommendation based on commission distribution

### Changed
- **Contestation Classification**: More aggressive logic to reduce "MODERATE CONTESTATION" cases
- **Ownership Attribution**: Better identification of clear ownership vs. contested deals

## [2025-08-15] - Enhanced Output Generation

### Added
- **deal_rationale.csv**: New comprehensive output file with stage breakdown and rationale
- **Stage Breakdown Columns**: Individual columns for each sales stage showing primary handler
- **Enhanced Rationale**: Detailed explanation of commission splits with stage participation

### Changed
- **Output Format**: More comprehensive and actionable commission analysis
- **Documentation**: Enhanced README and process documentation

## [2025-08-14] - Commission Calculation Consolidation

### Added
- **Unified Commission Logic**: Consolidated two separate commission calculation systems into one
- **Enhanced Documentation**: Comprehensive documentation of commission calculation process

### Changed
- **Code Structure**: Eliminated duplicate logic and improved maintainability
- **Commission Rules**: Standardized rules across all calculation methods

### Removed
- **Duplicate Files**: Eliminated redundant commission analysis scripts
- **Inconsistent Logic**: Standardized commission calculation approach

## [2025-08-13] - Channel Naming and Data Cleanup

### Added
- **Channel Renaming Support**: Updated database to handle Slack channel renaming events
- **Data Validation**: Improved validation of Slack data integrity

### Changed
- **Channel Mapping**: Corrected mapping for renamed channels (e.g., `na-bitsafe` → `bron-bitsafe`)
- **Database Schema**: Enhanced to track channel name changes over time

### Fixed
- **Data Consistency**: Resolved inconsistencies from channel renaming events
- **Commission Accuracy**: Improved accuracy by using correct channel names

## [2025-08-12] - Stage Detection Improvements

### Added
- **Expanded Keywords**: Enhanced keyword sets for each deal stage based on CBTC documentation
- **Stage Weight Adjustment**: Refined weights based on business importance

### Changed
- **Confidence Calculation**: Improved confidence scoring for better stage detection
- **Keyword Coverage**: More comprehensive keyword sets for accurate stage identification

## [2025-08-11] - Initial Commission System

### Added
- **Basic Commission Calculation**: Initial implementation of commission splitting logic
- **Stage Detection**: Keyword-based detection of sales stages in Slack messages
- **Output Generation**: Basic CSV output with commission percentages
- **Configuration System**: JSON-based configuration for stages, weights, and participants
