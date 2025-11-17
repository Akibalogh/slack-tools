# Google Calendar API Setup Guide

## Step 1: Google Cloud Console Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/

2. **Create or Select Project**:
   - Click the project dropdown at the top
   - Create a new project or select existing one
   - Note your project ID

3. **Enable Google Calendar API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click on it and press "Enable"

4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure OAuth consent screen first:
     - Choose "External" user type
     - Fill in app name: "Slack Tools ETL"
     - Add your email as test user
   - Choose "Desktop application"
   - Name it "Slack Tools Calendar Integration"
   - Click "Create"

5. **Download Credentials**:
   - Click the download button (⬇️) next to your new OAuth client
   - Save the JSON file as `calendar_credentials.json`
   - Place it in the `credentials/` folder

## Step 2: Replace Template File

Replace the template file `credentials/calendar_credentials.json` with your downloaded file.

## Step 3: Test the Integration

Run this command to test:

```bash
python3 -c "
from src.etl.integrations.google_calendar_integration import GoogleCalendarIntegration
calendar = GoogleCalendarIntegration()
print('Success!' if calendar.test_connection() else 'Failed - check credentials')
"
```

## Step 4: Run ETL with Real Data

Once authenticated, run the full ETL:

```bash
python3 -c "
from src.etl.etl_data_ingestion import DataETL
etl = DataETL(quick_mode=True)
etl.run_etl()
print('ETL completed with real calendar data!')
"
```

## Troubleshooting

### 400 Error
- **Cause**: Invalid or placeholder credentials
- **Fix**: Replace template with real Google Cloud Console credentials

### Authentication Error
- **Cause**: OAuth consent screen not configured
- **Fix**: Complete OAuth consent screen setup in Google Cloud Console

### Permission Denied
- **Cause**: Calendar API not enabled
- **Fix**: Enable Google Calendar API in Google Cloud Console

### No Meetings Found
- **Cause**: No meetings in date range or calendar access issues
- **Fix**: Check calendar permissions and date range

## Expected Results

Once properly configured, you should see:
- ✅ Real Google Calendar authentication successful
- 📅 Retrieved X real meetings from Google Calendar
- Real meeting data in ETL output
- Improved company data coverage

## Security Notes

- Never commit real credentials to git
- The `credentials/` folder is already in `.gitignore`
- Keep your client secret secure
- Use test users for development


