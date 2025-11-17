# HubSpot CRM Export Files

Place your HubSpot CRM export files in this directory.

## Supported File Formats
- CSV files (.csv)
- Excel files (.xlsx, .xls)

## Expected File Names
- deals.csv (or deals.xlsx) - Deal/opportunity data
- contacts.csv (or contacts.xlsx) - Contact data
- companies.csv (or companies.xlsx) - Company data

## File Structure
The ETL system will automatically detect and process files in this directory.
Make sure your CSV files have headers in the first row.

## Example Deal CSV Structure
```csv
Deal Name,Company,Deal Stage,Amount,Close Date,Owner,Description
```

## Example Contact CSV Structure
```csv
First Name,Last Name,Email,Company,Job Title,Phone
```

## Example Company CSV Structure
```csv
Company Name,Domain,Industry,City,State,Country
```

