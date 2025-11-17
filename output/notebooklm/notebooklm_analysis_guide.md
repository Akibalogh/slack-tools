# NotebookLM Analysis Guide

## Overview
This guide provides step-by-step instructions for uploading ETL data to NotebookLM and conducting comprehensive deal ownership analysis.

## Files to Upload to NotebookLM

### Required Files (Upload in Order)
1. **`notebooklm_integration_guide.md`** - System overview and context
2. **`business_context.md`** - Company background and deal stages
3. **`sales_team.md`** - Sales team structure and commission rules
4. **`company_mapping.csv`** - Complete company database
5. **`deal_stages.md`** - Deal stage definitions and progression
6. **`etl_output.txt`** - **MAIN DATA FILE** - Complete conversation data

### Optional Files (For Context)
- `data_sources.md` - Technical documentation about data sources
- Any archived ETL outputs from `archive/` folder for comparison

## Step-by-Step NotebookLM Setup

### 1. Create New NotebookLM Project
- Go to [NotebookLM](https://notebooklm.google.com)
- Click "New notebook"
- Name it "BitSafe Deal Ownership Analysis"

### 2. Upload Documentation Files First
Upload these files in order to establish context:
```
1. notebooklm_integration_guide.md
2. business_context.md  
3. sales_team.md
4. company_mapping.csv
5. deal_stages.md
```

### 3. Upload Main Data File
Upload the main ETL output:
```
6. etl_output.txt (from output/notebooklm/)
```

### 4. Verify Upload Success
Check that NotebookLM has processed:
- 113 companies
- Sales team information (Amy, Aki, Mayank, Addie)
- Deal stage definitions
- Commission rules

## Analysis Questions to Ask NotebookLM

### Basic Validation Questions
1. **"How many companies are in this dataset?"**
   - Expected: 113 companies

2. **"Who are the sales team members?"**
   - Expected: Amy, Aki, Mayank, Addie (all Account Executives)

3. **"What are the deal stages?"**
   - Expected: Lead, Qualified, Proposal, Negotiation, Closed Won, Closed Lost

### Deal Ownership Analysis
4. **"For each company with conversation data, who is the most likely deal owner based on message frequency and content?"**

5. **"Which companies have clear deal ownership patterns vs. unclear ownership?"**

6. **"For companies with multiple sales reps involved, how should commission be split?"**

### Data Quality Assessment
7. **"Which companies have insufficient conversation data to determine ownership?"**

8. **"Are there any patterns in how sales reps communicate with customers?"**

9. **"Which deal stages are most commonly discussed in conversations?"**

### Specific Company Analysis
10. **"Analyze the Allnodes conversations - who is the primary deal owner?"**
    - Expected: Should identify Aki as primary based on conversation patterns

11. **"For companies with both Slack and Telegram data, which channel shows more deal activity?"**

## Expected Analysis Results

### High-Quality Data Companies (Should Have Clear Ownership)
- **Allnodes** - Aki Balogh (extensive Telegram conversations)
- **Companies with 10+ messages** - Should show clear patterns

### Medium-Quality Data Companies
- **Companies with 3-9 messages** - May have ownership hints
- **Companies with only Slack OR only Telegram** - Limited but usable

### Low-Quality Data Companies (50+ companies with no data)
- **ALUM-LABS, CHAINSAFE, DIGIK, FIVE-NORTH, FOUNDINALS, GOMAESTRO, LAUNCHNODES, LITHIUM-DIGITAL, MODULO-FINANCE, MPCH, NODEMONSTERS, OBSIDIAN, PIER-TWO, REGISTER-LABS, TALL-OAK-MIDSTREAM, TENKAI, TRAKX, T-RIZE, UNLOCK-IT, XLABS** and variants

## Debugging Common Issues

### Issue: NotebookLM Says "No Data Found"
**Solution**: Check if `etl_output.txt` uploaded correctly. File should be ~2MB+ with 113 companies.

### Issue: NotebookLM Can't Identify Deal Owners
**Possible Causes**:
1. Sender names not showing (check for "Unknown" vs actual names)
2. Insufficient conversation data
3. No clear sales rep involvement

**Debug Steps**:
1. Ask: "Show me a sample conversation with sender names"
2. Ask: "Which companies have the most messages?"
3. Ask: "Can you identify any sales rep names in the conversations?"

### Issue: Commission Split Recommendations Seem Wrong
**Check**: Ask NotebookLM "What are the commission splitting rules?" to verify it understands the equal-split structure.

## Validation Checklist

After running analysis, verify:
- [ ] NotebookLM processed all 113 companies
- [ ] Sender names are actual names (not "Unknown")
- [ ] Can identify sales reps vs customers
- [ ] Deal ownership recommendations make sense
- [ ] Companies with no data are properly flagged
- [ ] Commission split logic follows equal-split rules

## Next Steps After Analysis

1. **Export Results**: Ask NotebookLM to provide a summary of deal ownership recommendations
2. **Identify Data Gaps**: Focus on companies with insufficient data
3. **Validate Recommendations**: Cross-check with your knowledge of actual deal ownership
4. **Iterate**: Update ETL data and re-upload if needed

## Troubleshooting

### If Upload Fails
- Check file size (NotebookLM has limits)
- Try uploading files individually
- Verify file encoding (should be UTF-8)

### If Analysis is Incomplete
- Ask more specific questions
- Provide additional context about specific companies
- Use the archived ETL outputs for comparison

### If Results Don't Match Expectations
- Verify the data quality in `etl_output.txt`
- Check if sender names are properly extracted
- Confirm conversation data completeness


