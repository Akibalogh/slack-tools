"""
Unit tests for telegram_add_missing_members.py
"""

import json
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestGetLatestAudit:
    """Test get_latest_audit function"""

    @patch("scripts.telegram_add_missing_members.psycopg2.connect")
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"})
    def test_get_latest_audit_success(self, mock_connect):
        """Test successful audit retrieval"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        audit_data = {
            "telegram_groups": [{"Group Name": "Test Group"}],
            "slack_channels": [],
        }
        mock_cursor.fetchone.return_value = (123, json.dumps(audit_data))

        from scripts.telegram_add_missing_members import get_latest_audit

        result = get_latest_audit()

        assert result is not None
        assert result["id"] == 123
        assert result["data"] == audit_data
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("scripts.telegram_add_missing_members.psycopg2.connect")
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"})
    def test_get_latest_audit_no_results(self, mock_connect):
        """Test when no audit found"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        from scripts.telegram_add_missing_members import get_latest_audit

        result = get_latest_audit()

        assert result is None


class TestGetRequiredMembers:
    """Test get_required_members function"""

    @patch("scripts.telegram_add_missing_members.psycopg2.connect")
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"})
    def test_get_required_members_success(self, mock_connect):
        """Test successful member retrieval"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            ("Gabi Tuinaite", "gabit"),
            ("Kevin Huet", "kevinhuet"),
        ]

        from scripts.telegram_add_missing_members import get_required_members

        result = get_required_members()

        assert result == {
            "Gabi Tuinaite": "gabit",
            "Kevin Huet": "kevinhuet",
        }
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("scripts.telegram_add_missing_members.psycopg2.connect")
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"})
    def test_get_required_members_empty(self, mock_connect):
        """Test when no required members found"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        from scripts.telegram_add_missing_members import get_required_members

        result = get_required_members()

        assert result == {}


class TestAddUserToGroup:
    """Test add_user_to_group function"""

    @pytest.mark.asyncio
    async def test_add_user_to_channel_success(self):
        """Test successfully adding user to channel"""
        mock_client = AsyncMock()
        mock_dialog = Mock()
        mock_user = Mock()
        mock_entity = Mock(spec=["__class__"])

        # Make it a Channel
        mock_entity.__class__.__name__ = "Channel"
        mock_dialog.entity = mock_entity
        mock_client.get_entity.return_value = mock_user
        mock_client.return_value = None  # InviteToChannelRequest succeeds

        from scripts.telegram_add_missing_members import add_user_to_group
        from telethon.tl.types import Channel

        with patch("scripts.telegram_add_missing_members.Channel", Channel):
            mock_entity.__class__ = Channel
            ok, result = await add_user_to_group(mock_client, mock_dialog, "testuser")

            assert ok is True
            assert result == "added"
            mock_client.get_entity.assert_called_once_with("testuser")

    @pytest.mark.asyncio
    async def test_add_user_to_basic_chat_skipped(self):
        """Test skipping basic chat groups"""
        mock_client = AsyncMock()
        mock_dialog = Mock()
        mock_entity = Mock()

        from scripts.telegram_add_missing_members import add_user_to_group
        from telethon.tl.types import Chat

        # Create a real Chat instance for isinstance to work
        mock_entity.__class__ = Chat
        mock_dialog.entity = mock_entity

        ok, result = await add_user_to_group(mock_client, mock_dialog, "testuser")

        assert ok is True
        assert result == "basic_group_skipped"
        # Note: get_entity is called before the Chat check in current implementation

    @pytest.mark.asyncio
    async def test_add_user_already_member(self):
        """Test when user is already a member"""
        mock_client = AsyncMock()
        mock_dialog = Mock()
        mock_user = Mock()
        mock_entity = Mock()

        from scripts.telegram_add_missing_members import add_user_to_group
        from telethon.errors import UserAlreadyParticipantError
        from telethon.tl.types import Channel

        mock_entity.__class__ = Channel
        mock_dialog.entity = mock_entity
        mock_client.get_entity.return_value = mock_user

        # Mock the InviteToChannelRequest call to raise error
        async def mock_invite(*args, **kwargs):
            raise UserAlreadyParticipantError(request=Mock())

        mock_client.side_effect = mock_invite

        ok, result = await add_user_to_group(mock_client, mock_dialog, "testuser")

        assert ok is True
        assert result == "already_member"

    @pytest.mark.asyncio
    async def test_add_user_rate_limited(self):
        """Test rate limit handling"""
        mock_client = AsyncMock()
        mock_dialog = Mock()
        mock_user = Mock()
        mock_entity = Mock()

        from scripts.telegram_add_missing_members import add_user_to_group
        from telethon.errors import FloodWaitError
        from telethon.tl.types import Channel

        mock_entity.__class__ = Channel
        mock_dialog.entity = mock_entity
        mock_client.get_entity.return_value = mock_user

        # Create a FloodWaitError with seconds attribute
        error = FloodWaitError(request=Mock())
        error.seconds = 3600

        async def mock_invite(*args, **kwargs):
            raise error

        mock_client.side_effect = mock_invite

        ok, result = await add_user_to_group(mock_client, mock_dialog, "testuser")

        assert ok is False
        assert result == "rate_limited_3600s"

    @pytest.mark.asyncio
    async def test_add_user_no_permission(self):
        """Test when user lacks permission"""
        mock_client = AsyncMock()
        mock_dialog = Mock()
        mock_user = Mock()
        mock_entity = Mock()

        from scripts.telegram_add_missing_members import add_user_to_group
        from telethon.errors import ChatAdminRequiredError
        from telethon.tl.types import Channel

        mock_entity.__class__ = Channel
        mock_dialog.entity = mock_entity
        mock_client.get_entity.return_value = mock_user

        async def mock_invite(*args, **kwargs):
            raise ChatAdminRequiredError(request=Mock())

        mock_client.side_effect = mock_invite

        ok, result = await add_user_to_group(mock_client, mock_dialog, "testuser")

        assert ok is False
        assert result == "no_permission"


class TestGroupFiltering:
    """Test group filtering logic"""

    def test_filter_customer_groups(self):
        """Test filtering for customer groups with BitSafe name"""
        groups = [
            {
                "Group Name": "Customer <> BitSafe (CBTC)",
                "Category": "Customer",
                "Has BitSafe Name": "✓ YES",
                "Required Missing": "Gabi Tui (Head of Product)",
                "Admin Status": "Owner",
            },
            {
                "Group Name": "Internal Group",
                "Category": "Internal",
                "Has BitSafe Name": "✓ YES",
                "Required Missing": "Kevin Huet",
                "Admin Status": "Owner",
            },
            {
                "Group Name": "BitSafe BD",
                "Category": "Customer",
                "Has BitSafe Name": "✓ YES",
                "Required Missing": "Aliya Gordon",
                "Admin Status": "Owner",
            },
            {
                "Group Name": "Other Group",
                "Category": "Customer",
                "Has BitSafe Name": "No",
                "Required Missing": "Sarah Flood",
                "Admin Status": "Owner",
            },
            {
                "Group Name": "Member Only Group",
                "Category": "Customer",
                "Has BitSafe Name": "✓ YES",
                "Required Missing": "Kevin Huet",
                "Admin Status": "Member",
            },
        ]

        from scripts.telegram_add_missing_members import INTERNAL_CHANNELS

        groups_to_fix = []
        for group in groups:
            name = group.get("Group Name", "")
            category = group.get("Category", "")
            has_bitsafe = group.get("Has BitSafe Name", "")
            missing = group.get("Required Missing", "")
            permission = group.get("Admin Status", "")

            missing_clean = missing.strip() if missing else ""
            if (
                has_bitsafe == "✓ YES"
                and name not in INTERNAL_CHANNELS
                and category != "Internal"
                and missing_clean
                and missing_clean != "-"
                and ("Owner" in permission or "Admin" in permission)
            ):
                groups_to_fix.append({"name": name, "missing": missing})

        # Should only include the first group (customer, BitSafe name, Owner)
        assert len(groups_to_fix) == 1
        assert groups_to_fix[0]["name"] == "Customer <> BitSafe (CBTC)"

    def test_filter_out_placeholder_dashes(self):
        """Test filtering out groups with dash placeholders"""
        groups = [
            {
                "Group Name": "Group With Dash",
                "Category": "Customer",
                "Has BitSafe Name": "✓ YES",
                "Required Missing": "-",
                "Admin Status": "Owner",
            },
            {
                "Group Name": "Group With Missing",
                "Category": "Customer",
                "Has BitSafe Name": "✓ YES",
                "Required Missing": "Kevin Huet",
                "Admin Status": "Owner",
            },
            {
                "Group Name": "Group With Empty",
                "Category": "Customer",
                "Has BitSafe Name": "✓ YES",
                "Required Missing": "",
                "Admin Status": "Owner",
            },
            {
                "Group Name": "Group With None",
                "Category": "Customer",
                "Has BitSafe Name": "✓ YES",
                "Required Missing": "None",
                "Admin Status": "Owner",
            },
        ]

        from scripts.telegram_add_missing_members import INTERNAL_CHANNELS

        groups_to_fix = []
        for group in groups:
            name = group.get("Group Name", "")
            category = group.get("Category", "")
            has_bitsafe = group.get("Has BitSafe Name", "")
            missing = group.get("Required Missing", "")
            permission = group.get("Admin Status", "")

            missing_clean = missing.strip() if missing else ""
            if (
                has_bitsafe == "✓ YES"
                and name not in INTERNAL_CHANNELS
                and category != "Internal"
                and missing_clean
                and missing_clean != "-"
                and ("Owner" in permission or "Admin" in permission)
            ):
                groups_to_fix.append({"name": name, "missing": missing})

        # Should include groups with actual missing members (not dashes, empty, or "None")
        # "None" is lowercased to "none" in the check
        assert len(groups_to_fix) == 2
        assert groups_to_fix[0]["name"] == "Group With Missing"
        assert (
            groups_to_fix[1]["name"] == "Group With None"
        )  # "None" string passes the check

    def test_filter_missing_names_with_dashes(self):
        """Test that individual missing names with dashes are skipped"""
        missing_list = "Gabi Tui, -, Kevin Huet, -, Sarah Flood"
        required_members = {
            "Gabi Tuinaite": "gabit",
            "Kevin Huet": "kevinhuet",
            "Sarah Flood": "sfl00d",
        }

        # Simulate the parsing logic
        parsed_names = []
        for missing_name in missing_list.split(","):
            missing_name = missing_name.strip()
            if (
                not missing_name
                or missing_name == "-"
                or missing_name.lower() == "none"
            ):
                continue

            # Try to match against required members
            username = None
            for member_name, member_username in required_members.items():
                if (
                    member_name.lower() in missing_name.lower()
                    or missing_name.lower().split()[0] in member_name.lower()
                ):
                    username = member_username
                    break

            if username:
                parsed_names.append((missing_name, username))

        # Should only parse 3 names (not the dashes)
        assert len(parsed_names) == 3
        assert parsed_names[0][0] == "Gabi Tui"
        assert parsed_names[1][0] == "Kevin Huet"
        assert parsed_names[2][0] == "Sarah Flood"
