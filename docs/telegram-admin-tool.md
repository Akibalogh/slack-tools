# Telegram Admin Tool

Unified command-line tool for common Telegram group administration tasks.

## Features

- 🔍 **Find Users** - Search for any user across all your Telegram groups
- 🚫 **Remove Users** - Bulk remove users from groups where you have admin rights
- 👑 **Ownership Management** - Generate ownership transfer request messages
- ✏️  **Bulk Rename** - Rename multiple groups with pattern matching or JSON mappings
- 📊 **Reports** - Generate Excel reports for all operations

## Installation

```bash
# Install dependencies
pip install telethon python-dotenv pandas openpyxl

# Configure environment variables in .env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone
TELEGRAM_PASSWORD=your_2fa_password
```

## Usage

### Find a User

Search for a user across all your Telegram groups and check your admin status:

```bash
python3 scripts/telegram_admin.py find-user --username nftaddie
```

**Output:**
- Lists all groups where the user is present
- Shows your admin status in each group (Owner / Admin / Member)
- Generates Excel report: `output/user_search_<username>.xlsx`

### Remove a User

Remove a user from groups where you have admin/owner rights:

```bash
# Remove from all groups where you have permission
python3 scripts/telegram_admin.py remove-user --username nftaddie

# Remove from specific groups only
python3 scripts/telegram_admin.py remove-user --username nftaddie --groups groups.txt
```

**groups.txt format** (one group name per line):
```
Group Name 1
Group Name 2
Group Name 3
```

### Request Ownership Transfer

Generate messages to request ownership transfer from current group owners:

```bash
python3 scripts/telegram_admin.py request-ownership --groups groups.txt
```

**Output:**
- Identifies current owner of each group
- Generates copy-paste messages: "Hi @owner - could you transfer ownership to me?"
- Saves to: `output/ownership_requests.txt`

### Rename Groups

#### Pattern-based renaming

Replace a pattern across all group names:

```bash
# Replace "iBTC" with "BitSafe (CBTC)" in all group names
python3 scripts/telegram_admin.py rename --pattern "iBTC" --replace "BitSafe (CBTC)"

# Remove " (new)" suffix
python3 scripts/telegram_admin.py rename --pattern " (new)" --replace ""
```

#### JSON mapping-based renaming

For precise control, use a JSON mapping file:

```bash
python3 scripts/telegram_admin.py rename --mapping renames.json
```

**renames.json format:**
```json
{
  "Old Group Name 1": "New Group Name 1",
  "Old Group Name 2": "New Group Name 2",
  "Forteus | iBTC": "Forteus <> BitSafe (CBTC)"
}
```

## Rate Limiting

Telegram has built-in rate limits:
- **Renames**: ~10 per 15 minutes
- **Member actions**: Varies by account age and activity

The tool will automatically report rate-limited operations. For large batches, run the command multiple times with 15-minute gaps.

## Common Workflows

### Remove Former Employee

1. **Find** where they are:
   ```bash
   python3 scripts/telegram_admin.py find-user --username formeremployee
   ```

2. **Remove** from groups you control:
   ```bash
   python3 scripts/telegram_admin.py remove-user --username formeremployee
   ```

3. **Request ownership** for groups you don't control:
   ```bash
   # Save groups needing transfer to file
   python3 scripts/telegram_admin.py find-user --username formeremployee > found.txt
   # Edit found.txt to keep only "Member" groups
   python3 scripts/telegram_admin.py request-ownership --groups found.txt
   ```

### Rebrand Groups

1. **Test** with a pattern replacement:
   ```bash
   python3 scripts/telegram_admin.py rename --pattern "OldName" --replace "NewName"
   ```

2. For **precise control**, create a mapping JSON and use:
   ```bash
   python3 scripts/telegram_admin.py rename --mapping my_renames.json
   ```

### Audit Group Access

1. **Find all groups** where someone has access:
   ```bash
   python3 scripts/telegram_admin.py find-user --username person
   ```

2. **Check the generated Excel** report:
   - `output/user_search_person.xlsx`
   - Filter by "Admin Status" column
   - Identify gaps in access control

## Troubleshooting

### "database is locked" Error

Kill background processes using the Telegram session:

```bash
pkill -f "python3.*telegram"
sleep 2
# Try your command again
```

### "Invalid object ID" Error

This occurs when:
- Group was recently renamed (use new name)
- You don't have access to the group
- Group type doesn't support the operation

### Authentication Issues

If you need to re-authenticate:

```bash
# Remove session file
rm telegram_session.session

# Next command will prompt for phone code
python3 scripts/telegram_admin.py find-user --username test
```

## Security Notes

- **Session files** (`*.session`) are sensitive - never commit to git
- **2FA password** is stored in `.env` - keep this secure
- **Ownership transfer** cannot be undone - verify before requesting
- **Removals** are permanent - user must be re-invited to rejoin

## Integration with Other Tools

This tool works alongside:
- `customer_group_audit.py` - Comprehensive audit of all groups
- `add_members_to_channels.py` - Bulk add members to Slack channels

For full automation workflows, see: `docs/admin-workflows.md`

## Examples

### Example 1: Clean up after employee departure

```bash
# 1. Find all their groups
python3 scripts/telegram_admin.py find-user --username exemployee

# 2. Remove from groups you control
python3 scripts/telegram_admin.py remove-user --username exemployee

# 3. Generate ownership requests for the rest
echo "Group A\nGroup B\nGroup C" > need_ownership.txt
python3 scripts/telegram_admin.py request-ownership --groups need_ownership.txt
```

### Example 2: Standardize group naming

```bash
# Create mapping file
cat > renames.json << 'EOF'
{
  "Old Name 1": "Standardized Name 1",
  "Old Name 2": "Standardized Name 2"
}
EOF

# Execute renames
python3 scripts/telegram_admin.py rename --mapping renames.json
```

### Example 3: Audit contractor access

```bash
# Check where contractor has access
python3 scripts/telegram_admin.py find-user --username contractor123

# Open the Excel report
open output/user_search_contractor123.xlsx

# Filter for groups where they're admin/owner
# Verify this matches their contract scope
```

## Tips

- **Always test** with a small subset first
- **Save reports** before making changes
- **Document reasons** for ownership transfers in a separate doc
- **Coordinate** with team before bulk removals
- **Check twice**, execute once - especially for irreversible operations

## Related Documentation

- [Customer Group Audit](customer-group-audit.md) - Full audit of Slack & Telegram
- [Add Members Tool](add-members-tool.md) - Bulk add to Slack channels
- [Slack Export Tool](slack-export-howto.md) - Export Slack channel history

---

*For questions or issues, see the main project README or create an issue.*

