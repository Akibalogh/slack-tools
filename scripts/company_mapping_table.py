#!/usr/bin/env python3
"""
Company Mapping Table Generator

Generates a comprehensive table showing:
- Company name
- Slack channel name (if exists)
- Telegram group name (if exists)
- Calendar entries (if exist)

Uses display names instead of internal IDs for better readability.
"""

import json
import os
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class CompanyMappingTable:
    """Generate comprehensive company mapping table across all platforms"""

    def __init__(self, db_path: str = "repsplit.db"):
        self.db_path = db_path
        self.companies = {}

    def load_slack_channels(self) -> Dict[str, str]:
        """Load Slack channels with display names"""
        if not os.path.exists(self.db_path):
            print(f"⚠️  Database not found: {self.db_path}")
            return {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all company channels with message counts (not just bitsafe ones)
        cursor.execute(
            """
            SELECT c.name, COUNT(m.id) as msg_count
            FROM conversations c 
            LEFT JOIN messages m ON c.conv_id = m.conv_id 
            WHERE c.name NOT LIKE '%general%' 
              AND c.name NOT LIKE '%random%' 
              AND c.name NOT LIKE '%business%'
              AND c.name NOT LIKE '%validator%'
              AND c.name NOT LIKE '%eng%'
              AND c.name NOT LIKE '%gsf%'
              AND c.name NOT LIKE '%dlc%'
              AND c.name NOT LIKE '%ibtc%'
              AND c.name NOT LIKE '%cbtc%'
              AND c.name NOT LIKE '%canton%'
              AND c.name NOT LIKE '%utility%'
              AND c.name NOT LIKE '%vault%'
              AND c.name NOT LIKE '%incident%'
              AND c.name NOT LIKE '%runbook%'
              AND c.name NOT LIKE '%testnet%'
              AND c.name NOT LIKE '%mainnet%'
            GROUP BY c.conv_id, c.name 
            ORDER BY msg_count DESC
        """
        )

        channels = cursor.fetchall()
        conn.close()

        # Convert to company mapping
        slack_mapping = {}
        for channel_name, msg_count in channels:
            if channel_name and msg_count > 0:
                # Extract company name (remove -bitsafe suffix)
                company_name = (
                    channel_name.replace("-bitsafe", "")
                    .replace("-cbtc", "")
                    .replace("-ibtc", "")
                )
                # Convert to title case for display
                display_name = " ".join(
                    word.capitalize() for word in company_name.split("-")
                )
                slack_mapping[display_name] = channel_name

        return slack_mapping

    def load_telegram_groups(self) -> Dict[str, str]:
        """Load Telegram groups with display names"""
        # Check if telegram mapping file exists
        mapping_files = [
            "docs/telegram/crm_telegram_mapping.md",
            "docs/telegram/telegram_match_verification.md",
            "docs/telegram/corrected_telegram_mapping.md",
        ]

        telegram_mapping = {}

        for filename in mapping_files:
            if os.path.exists(filename):
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Extract company -> group mappings
                    lines = content.split("\n")
                    for line in lines:
                        # Pattern: Company → chat_XXXX
                        if " → " in line and "chat_" in line:
                            parts = line.split(" → ")
                            if len(parts) == 2:
                                company = (
                                    parts[0].strip().replace("**", "").replace("`", "")
                                )
                                chat_dir = parts[1].strip().replace("`", "")

                                # Extract company name directly from the line
                                extracted_company = (
                                    self._extract_company_from_telegram_name(company)
                                )
                                if extracted_company and self._is_company_name(
                                    extracted_company
                                ):
                                    telegram_mapping[extracted_company] = chat_dir

                        # Pattern: Company | Group Name | Match Type
                        elif (
                            " | " in line
                            and "Match Type" not in line
                            and "Company" not in line
                        ):
                            parts = line.split(" | ")
                            if len(parts) >= 2:
                                company = parts[0].strip()
                                group_name = parts[1].strip()
                                if (
                                    group_name
                                    and group_name != "Chat Dir"
                                    and not group_name.startswith("chat_")
                                ):
                                    # Extract company name from the group name using the new method
                                    extracted_company = (
                                        self._extract_company_from_telegram_name(
                                            group_name
                                        )
                                    )
                                    if extracted_company and self._is_company_name(
                                        extracted_company
                                    ):
                                        telegram_mapping[extracted_company] = group_name

                except Exception as e:
                    print(f"⚠️  Error reading {filename}: {e}")

        return telegram_mapping

    def _extract_company_from_telegram_name(self, telegram_name: str) -> str:
        """Extract company name from Telegram group naming patterns like 'BitSafe <> CompanyName'"""
        if not telegram_name:
            return ""

        # Remove HTML entities and clean up
        clean_name = (
            telegram_name.replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
        )
        clean_name = clean_name.replace("&lt;&gt;", "<>").replace("&gt;&lt;", "><")

        # Skip DMs and individual conversations - only process group names
        dm_indicators = ["Proof", "DM", "Direct", "Message", "Chat", "Conversation"]
        if any(ind.lower() in clean_name.lower() for ind in dm_indicators):
            # Check if it looks like a person's name pattern
            import re

            person_pattern = r"^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$"
            if re.match(person_pattern, clean_name):
                return ""  # Skip DMs with person names

        # More comprehensive patterns to extract company names from
        patterns = [
            # "CompanyName <> BitSafe" -> "CompanyName" (most common pattern)
            r"([^<>()]+?)\s*<>\s*BitSafe",
            # "BitSafe <> CompanyName" -> "CompanyName"
            r"BitSafe\s*<>\s*([^<>()]+?)(?:\s*<>|$)",
            # "CompanyName - BitSafe" -> "CompanyName"
            r"([^-()]+?)\s*-\s*BitSafe",
            # "BitSafe - CompanyName" -> "CompanyName"
            r"BitSafe\s*-\s*([^-()]+?)(?:\s*-|$)",
            # "CompanyName / BitSafe" -> "CompanyName"
            r"([^/()]+?)\s*/\s*BitSafe",
            # "BitSafe / CompanyName" -> "CompanyName"
            r"BitSafe\s*/\s*([^/()]+?)(?:\s*/|$)",
            # "CompanyName | BitSafe" -> "CompanyName"
            r"([^|()]+?)\s*\|\s*BitSafe",
            # "BitSafe | CompanyName" -> "CompanyName"
            r"BitSafe\s*\|\s*([^|()]+?)(?:\s*\||$)",
            # "CompanyName x BitSafe" -> "CompanyName" (handle double spaces)
            r"([^x()]+?)\s+x\s+BitSafe",
            # "BitSafe x CompanyName" -> "CompanyName" (handle double spaces)
            r"BitSafe\s+x\s+([^x()]+?)(?:\s+x|$)",
            # "CompanyName & BitSafe" -> "CompanyName"
            r"([^&()]+?)\s*&\s*BitSafe",
            # "BitSafe & CompanyName" -> "CompanyName"
            r"BitSafe\s*&\s*([^&()]+?)(?:\s*&|$)",
            # Handle P2P.org pattern specifically
            r"([^<>()]+?\.org)\s*<>\s*BitSafe",
            r"BitSafe\s*<>\s*([^<>()]+?\.org)(?:\s*<>|$)",
            # Handle company names with spaces and special characters
            r"([^<>()]+?)\s+Group\s*<>\s*BitSafe",
            r"BitSafe\s*<>\s*([^<>()]+?)\s+Group(?:\s*<>|$)",
        ]

        import re

        for pattern in patterns:
            match = re.search(pattern, clean_name, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                # Clean up the extracted name
                company_name = re.sub(r"\s+", " ", company_name)  # Normalize whitespace
                company_name = company_name.strip()
                # Remove common prefixes/suffixes that aren't company names
                company_name = re.sub(
                    r"^(Khaled Verjee|Tally|Nico|Chris|John|Jonathan|Pinar|Karim|Mákkidamia|Levente|Simran|Joris|Klint|AlexC@|Nenter @|Alessio|Mike|Daniel|Faizan|Dom|Mateusz|Joo|Mihir|Gattman|PumpkinSeed|Ari|Yiannis|Jesse|Dim|Rex|Emmett|Anna|Dae|Luca|Trey|Jasminer|Forbole|Uwi|Nenter|IntellectEU|DeFiZoo\.fi|Pink Finance|Coinsummer|Chainup|F2pool|iPollo/Bitrise|Waterdrip|GBI|AngelHack|Superset|OKX DeFi|Solana DeFi|Ethereum Hungary|Harvard Blockchain|Magyar Internet 3|TRGC Familia|🇨🇭STS)\s+",
                    "",
                    company_name,
                    flags=re.IGNORECASE,
                )
                company_name = company_name.strip()
                if company_name and len(company_name) > 2:
                    return company_name

        # If no pattern matches, return the original name
        return clean_name.strip()

    def _is_company_name(self, name: str) -> bool:
        """Check if a name looks like a company name rather than an individual or DM"""
        # Clean the name first
        clean_name = name.replace("**", "").replace("`", "").strip()

        # Skip if empty
        if not clean_name:
            return False

        # Skip individual names (usually contain personal identifiers)
        individual_indicators = [
            "@",
            "&lt;&gt;",
            "&amp;",
            "&apos;",
            "&quot;",
            "&gt;",
            "&lt;",
        ]

        # Skip if contains personal indicators
        for indicator in individual_indicators:
            if indicator in clean_name:
                return False

        # Skip DMs - look for patterns that indicate individual conversations
        dm_indicators = ["Proof", "DM", "Direct", "Message", "Chat", "Conversation"]

        # Skip if it looks like a DM with a person's name
        if any(ind.lower() in clean_name.lower() for ind in dm_indicators):
            # Additional check: if it contains what looks like a person's name pattern
            # Look for patterns like "FirstName LastName" or "FirstName LastName Proof"
            import re

            person_pattern = r"^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$"
            if re.match(person_pattern, clean_name):
                return False

        # Keep company-like names
        company_indicators = [
            "Labs",
            "Capital",
            "Group",
            "Foundation",
            "Protocol",
            "DAO",
            "DeFi",
            "Finance",
            "Ventures",
            "Partners",
            "Systems",
            "Technologies",
            "Solutions",
            "Network",
            "Exchange",
            "Trading",
            "Investment",
            "Asset",
            "Blockchain",
            "Crypto",
            "BitSafe",
            "iBTC",
            "cBTC",
            "dlcBTC",
            "BitSafe",
            "Canton",
            # Add specific companies we know exist
            "Allnodes",
            "Republic",
            "Nethermind",
            "7Ridge",
            "Chainsafe",
            "Redstone",
            "Sendit",
            "Mpch",
            "Register Labs",
            "Chata Ai",
            "Ordinals Foundation",
            "Blockdaemon",
            "Blockandbones",
            "Blackmanta",
            "Blacksand",
            "Brale",
            "Cense",
            "Chainexperts",
            "Copper",
            "Cygnet",
            "Digik",
            "Entropydigital",
            "Five North",
            "G20",
            "Gateway",
            "Hashrupt",
            "Hlt",
            "Integraate",
            "Ipblock",
            "Kaiko",
            "Kaleido",
            "Komonode",
            "Launchnodes",
            "Levl",
            "Lightshift",
            "Lithiumdigital",
            "Luganodes",
            "Maestro",
            "Matrixedlink",
            "Mintify",
            "Mlabs",
            "Modulo Finance",
            "Mse",
            "Neogenesis",
            "Nodemonster",
            "Noders",
            "Notabene",
            "Novaprime",
            "Obsidian",
            "Openblock",
            "P2p",
            "Palladium",
            "Pathrock",
            "Proof",
            "Rwaxyz",
            "Sbc",
            "T Rize",
            "Tall Oak Midstream",
            "Temple",
            "Tenkai",
            "Thetanuts",
            "Trakx",
            "Ubyx",
            "Vigilmarkets",
            "Xlabs",
            "Zeconomy",
        ]

        for indicator in company_indicators:
            if indicator.lower() in clean_name.lower():
                return True

        # Keep names that look like companies (multiple words, longer names)
        if len(clean_name) > 6 and (
            " " in clean_name or "-" in clean_name or "_" in clean_name
        ):
            return True

        # Keep names that are likely companies (not just single words that could be people)
        if len(clean_name) > 8:
            return True

        # Keep names with company-like patterns
        if any(char in clean_name for char in ["&", "x", "/", "(", ")"]):
            return True

        return False

    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for consistent matching"""
        if not name:
            return ""

        # Convert to lowercase and remove common suffixes
        normalized = name.lower().strip()

        # Remove common suffixes that appear in Slack channels
        suffixes = ["-bitsafe", "-cbtc", "-ibtc", "-minter", "-validator", "-mainnet"]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break

        # Replace common separators with spaces
        normalized = normalized.replace("-", " ").replace("_", " ")

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        # Handle special cases for better matching
        # Remove common words that don't help with matching
        common_words = ["the", "and", "&", "inc", "llc", "ltd", "corp", "company"]
        words = normalized.split()
        filtered_words = [
            word for word in words if word not in common_words and len(word) > 1
        ]
        normalized = " ".join(filtered_words)

        # Handle specific company name variations
        # P2P.org -> P2P
        if normalized.endswith(".org"):
            normalized = normalized[:-4]  # Remove .org suffix
        # Proof Group -> Proof
        if normalized.endswith(" group"):
            normalized = normalized[:-6]  # Remove ' group' suffix
        # Mintify variations
        elif "mintify" in normalized:
            normalized = "mintify"

        return normalized

    def _get_telegram_group_name(self, chat_dir: str, content: str) -> Optional[str]:
        """Get the actual group name from chat directory by searching the mapping file"""
        try:
            # Read the mapping file directly to find the company name
            mapping_files = [
                "docs/telegram/crm_telegram_mapping.md",
                "docs/telegram/telegram_match_verification.md",
                "docs/telegram/corrected_telegram_mapping.md",
            ]

            for mapping_file in mapping_files:
                if os.path.exists(mapping_file):
                    with open(mapping_file, "r", encoding="utf-8") as f:
                        mapping_content = f.read()

                    # Look for the specific chat directory in the mapping
                    lines = mapping_content.split("\n")
                    for line in lines:
                        if chat_dir in line and "→" in line:
                            # Extract company name from format: "**CompanyName &lt;&gt; BitSafe** → `chat_XXXX`"
                            if "**" in line:
                                company_part = line.split("→")[0].strip()
                                company_part = company_part.replace("**", "").replace(
                                    "*", ""
                                )

                                # Extract just the company name (before any separator)
                                if "&lt;&gt;" in company_part:
                                    company_name = company_part.split("&lt;&gt;")[
                                        0
                                    ].strip()
                                elif " - " in company_part:
                                    company_name = company_part.split(" - ")[0].strip()
                                elif " / " in company_part:
                                    company_name = company_part.split(" / ")[0].strip()
                                elif " | " in company_part:
                                    company_name = company_part.split(" | ")[0].strip()
                                elif " x " in company_part:
                                    company_name = company_part.split(" x ")[0].strip()
                                elif " & " in company_part:
                                    company_name = company_part.split(" & ")[0].strip()
                                else:
                                    company_name = company_part.strip()

                                if company_name and company_name != "Chat Dir":
                                    # Clean up the company name - remove leading dashes and normalize
                                    company_name = company_name.strip()
                                    if company_name.startswith("- "):
                                        company_name = company_name[2:].strip()

                                    return company_name
        except Exception as e:
            pass  # Silently fail and return placeholder

        # If no readable name found, return a more descriptive placeholder
        return f"Telegram Group ({chat_dir})"

    def load_calendar_entries(self) -> Dict[str, List[str]]:
        """Load calendar entries for companies from database"""
        calendar_mapping = {}

        try:
            # Connect to the database
            conn = sqlite3.connect("repsplit.db")
            cursor = conn.cursor()

            # Query calendar meetings grouped by company
            cursor.execute(
                """
                SELECT company_name, meeting_title, meeting_date, duration_minutes
                FROM calendar_meetings 
                ORDER BY company_name, meeting_date DESC
            """
            )

            meetings = cursor.fetchall()

            # Group meetings by company
            company_meetings = {}
            for company_name, title, date, duration in meetings:
                if company_name not in company_meetings:
                    company_meetings[company_name] = []

                # Format meeting summary
                summary = f"{title} ({date}, {duration}min)"
                company_meetings[company_name].append(summary)

            # Take first 3 meetings per company for display
            for company_name, meeting_list in company_meetings.items():
                calendar_mapping[company_name] = meeting_list[:3]

            conn.close()
            return calendar_mapping

        except Exception as e:
            print(f"⚠️  Error reading calendar data from database: {e}")
            return {}

    def load_wallet_data(self) -> Dict[str, Dict]:
        """Load wallet data for companies from database"""
        wallet_mapping = {}

        try:
            # Connect to the database
            conn = sqlite3.connect("repsplit.db")
            cursor = conn.cursor()

            # Query wallet information
            cursor.execute(
                """
                SELECT company_name, status, fund_ownership, billing_wallet, 
                       external_customer_id, current_deposit, total_paid
                FROM company_wallets 
                ORDER BY company_name
            """
            )

            wallets = cursor.fetchall()

            for (
                company_name,
                status,
                fund_ownership,
                billing_wallet,
                external_id,
                deposit,
                paid,
            ) in wallets:
                # Normalize company name for matching
                normalized_name = self._normalize_company_name_for_wallet(company_name)

                if normalized_name:
                    wallet_mapping[normalized_name] = {
                        "status": status,
                        "fund_ownership": fund_ownership,
                        "billing_wallet": billing_wallet,
                        "external_customer_id": external_id,
                        "current_deposit": deposit,
                        "total_paid": paid,
                    }

            conn.close()
            return wallet_mapping

        except Exception as e:
            print(f"⚠️  Error reading wallet data from database: {e}")
            return {}

    def _normalize_company_name_for_wallet(self, wallet_company_name: str) -> str:
        """Normalize wallet company names to match company mapping names"""
        # Remove common suffixes and clean up
        name = wallet_company_name.strip()

        # Handle specific cases
        if "SendIt CantonWallet" in name:
            return "Sendit"
        elif "Send.It" in name:
            return "Sendit"
        elif "Redstone" in name:
            return "Redstone"
        elif "Meria" in name:
            return "Meria"
        elif "Komonode" in name:
            return "Komonode"
        elif "T-RIZE" in name:
            return "T-RIZE"
        elif "T Rize" in name:
            return "T-RIZE"
        elif "Tall Oak Midstream" in name:
            return "Tall Oak Midstream"
        elif "Obsidian" in name:
            return "Obsidian"
        elif "Mintify" in name:
            return "Mintify"
        elif "P2P" in name:
            return "P2P"
        elif "Linkpool" in name:
            return "Linkpool"
        elif "Unlock It" in name:
            return "Unlock It"
        elif "B2C2" in name:
            return "B2C2"
        elif "Path Rock" in name:
            return "Path Rock"
        elif "OpenVector" in name or "Cypherock" in name:
            return "OpenVector (Cypherock)"
        elif "SenseiNode" in name:
            return "SenseiNode"
        elif "POPS" in name:
            return "POPS"

        # General cleanup
        name = name.replace("CantonWallet", "").strip()
        name = name.replace("minter", "").strip()
        name = name.replace("validator", "").strip()
        name = name.replace("-minter", "").strip()
        name = name.replace("-validator", "").strip()

        # Remove extra spaces and clean up
        name = re.sub(r"\s+", " ", name).strip()

        return name

    def _find_company_matches(
        self, slack_companies: Dict[str, str], telegram_companies: Dict[str, str]
    ) -> Dict[str, tuple]:
        """Find matching companies between Slack and Telegram using normalized names"""
        matches = {}

        # Create normalized mappings
        slack_normalized = {}
        for display_name, channel_name in slack_companies.items():
            normalized = self._normalize_company_name(display_name)
            if normalized:
                slack_normalized[normalized] = (display_name, channel_name)

        telegram_normalized = {}
        for company_name, group_name in telegram_companies.items():
            normalized = self._normalize_company_name(company_name)
            if normalized:
                telegram_normalized[normalized] = (company_name, group_name)

        # Find exact matches first
        for normalized_name in slack_normalized:
            if normalized_name in telegram_normalized:
                slack_display, slack_channel = slack_normalized[normalized_name]
                telegram_company, telegram_group = telegram_normalized[normalized_name]
                matches[normalized_name] = (
                    slack_display,
                    slack_channel,
                    telegram_company,
                    telegram_group,
                )

        # Find partial matches for companies that didn't get exact matches
        for slack_norm, (slack_display, slack_channel) in slack_normalized.items():
            if slack_norm not in matches:  # Skip if already matched
                for telegram_norm, (
                    telegram_company,
                    telegram_group,
                ) in telegram_normalized.items():
                    if telegram_norm not in [
                        m[2] for m in matches.values()
                    ]:  # Skip if already matched
                        # Check if one name contains the other (partial match)
                        if (
                            (slack_norm in telegram_norm or telegram_norm in slack_norm)
                            and len(slack_norm) > 3
                            and len(telegram_norm) > 3
                        ):
                            matches[f"{slack_norm}_partial"] = (
                                slack_display,
                                slack_channel,
                                telegram_company,
                                telegram_group,
                            )

                            break

        return matches

    def generate_mapping_table(self) -> str:
        """Generate the complete mapping table"""
        print("🔍 Loading company data from all sources...")

        # Load data from all sources
        slack_channels = self.load_slack_channels()
        telegram_groups = self.load_telegram_groups()
        calendar_entries = self.load_calendar_entries()
        wallet_data = self.load_wallet_data()

        # Process Telegram groups to extract company names
        telegram_companies = {}
        for chat_dir, content in telegram_groups.items():
            company_name = self._get_telegram_group_name(chat_dir, content)
            if company_name and self._is_company_name(company_name):
                telegram_companies[company_name] = chat_dir

        # Find company matches using improved normalization
        company_matches = self._find_company_matches(slack_channels, telegram_companies)

        # Combine all company names
        all_companies = set()
        all_companies.update(slack_channels.keys())
        all_companies.update(telegram_companies.keys())
        all_companies.update(calendar_entries.keys())

        # Sort companies alphabetically
        sorted_companies = sorted(all_companies, key=str.lower)

        print(f"📊 Found {len(sorted_companies)} companies across all platforms")
        print(f"   Slack channels: {len(slack_channels)}")
        print(f"   Telegram groups: {len(telegram_groups)}")
        print(f"   Telegram companies: {len(telegram_companies)}")
        print(f"   Calendar entries: {len(calendar_entries)}")
        print(f"   Overlaps (Slack + Telegram): {len(company_matches)}")

        # Generate table
        table_lines = []
        table_lines.append("# Company Mapping Table")
        table_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        table_lines.append("")

        # Show summary first
        table_lines.append("## Summary")
        table_lines.append(f"- **Total Companies**: {len(sorted_companies)}")
        table_lines.append(f"- **With Slack Data**: {len(slack_channels)}")
        table_lines.append(f"- **With Telegram Data**: {len(telegram_companies)}")
        table_lines.append(f"- **With Calendar Data**: {len(calendar_entries)}")
        table_lines.append(f"- **Overlaps (Slack + Telegram)**: {len(company_matches)}")
        table_lines.append("")

        # Show overlap companies first
        if company_matches:
            table_lines.append("## Companies with Both Slack and Telegram Data")
            table_lines.append(
                "| Company | Slack Channel | Telegram Group | Calendar Entries |"
            )
            table_lines.append(
                "|---------|---------------|----------------|------------------|"
            )

            for normalized_name, (
                slack_display,
                slack_channel,
                telegram_company,
                telegram_group,
            ) in sorted(company_matches.items()):
                calendar_info = calendar_entries.get(slack_display, [])

                # Format calendar entries
                if calendar_info:
                    calendar_display = "<br>".join(
                        calendar_info[:2]
                    )  # Show first 2 meetings
                    if len(calendar_info) > 2:
                        calendar_display += f"<br>... and {len(calendar_info) - 2} more"
                else:
                    calendar_display = ""

                table_lines.append(
                    f"| **{slack_display}** (Overlap) | {slack_channel} | {telegram_group} | {calendar_display} |"
                )

            table_lines.append("")

        # Show wallet companies first (target companies)
        wallet_companies = set(wallet_data.keys())
        if wallet_companies:
            table_lines.append("## 🎯 Target Companies (With Wallet Data)")
            table_lines.append(
                "| Company | Slack Channel | Telegram Group | Calendar Entries | Wallet Status |"
            )
            table_lines.append(
                "|---------|---------------|----------------|------------------|---------------|"
            )

            for company in sorted(wallet_companies, key=str.lower):
                # Skip BitSafe (our company)
                if company.lower() in ["bitsafe", "bitsafe-minter"]:
                    continue

                slack_name = slack_channels.get(company, "")
                telegram_name = telegram_companies.get(company, "")
                calendar_info = calendar_entries.get(company, [])
                wallet_info = wallet_data.get(company, {})

                # Handle specific company corrections
                if company == "Redstone":
                    slack_name = "redstone-bitsafe"  # User confirmed Redstone has Slack
                elif company == "POPS":
                    telegram_name = (
                        "POPS Telegram Group"  # User confirmed POPS has Telegram
                    )
                elif company == "Path Rock":
                    slack_name = (
                        "pathrock-bitsafe"  # User confirmed Path Rock has Slack
                    )
                elif company == "OpenVector (Cypherock)":
                    slack_name = (
                        "openvector-bitsafe"  # User confirmed OpenVector has Slack
                    )
                elif company == "SenseiNode":
                    telegram_name = "BitSafe <> SenseiNode"  # Actual Telegram group name from mapping

                # Format calendar entries
                if calendar_info:
                    calendar_display = "<br>".join(
                        calendar_info[:2]
                    )  # Show first 2 meetings
                    if len(calendar_info) > 2:
                        calendar_display += f"<br>... and {len(calendar_info) - 2} more"
                else:
                    calendar_display = ""

                # Format wallet information
                wallet_display = ""
                if wallet_info:
                    status = wallet_info.get("status", "")
                    fund_ownership = wallet_info.get("fund_ownership", "")
                    deposit = wallet_info.get("current_deposit", "0")
                    paid = wallet_info.get("total_paid", "0")

                    wallet_display = (
                        f"{status} ({fund_ownership}) - {deposit} CC / {paid} CC"
                    )

                # Clean up names for table display
                slack_display = slack_name if slack_name else ""
                telegram_display = telegram_name if telegram_name else ""

                # Highlight overlaps
                is_overlap = any(
                    slack_display == match[1] for match in company_matches.values()
                )
                if is_overlap:
                    company_display = f"**{company}** (Overlap)"
                else:
                    company_display = company

                table_lines.append(
                    f"| {company_display} | {slack_display} | {telegram_display} | {calendar_display} | {wallet_display} |"
                )

            table_lines.append("")

            # Show coverage summary for wallet companies (excluding BitSafe)
            wallet_companies_filtered = [
                c
                for c in wallet_companies
                if c.lower() not in ["bitsafe", "bitsafe-minter"]
            ]
            wallet_with_slack = sum(
                1
                for company in wallet_companies_filtered
                if slack_channels.get(company, "")
                or company in ["Redstone", "Path Rock", "OpenVector (Cypherock)"]
            )
            wallet_with_telegram = sum(
                1
                for company in wallet_companies_filtered
                if telegram_companies.get(company, "")
                or company in ["POPS", "SenseiNode"]
            )
            wallet_with_calendar = sum(
                1
                for company in wallet_companies_filtered
                if calendar_entries.get(company, [])
            )
            wallet_with_both = sum(
                1
                for company in wallet_companies_filtered
                if (
                    slack_channels.get(company, "")
                    or company in ["Redstone", "Path Rock", "OpenVector (Cypherock)"]
                )
                and (
                    telegram_companies.get(company, "")
                    or company in ["POPS", "SenseiNode"]
                )
                and calendar_entries.get(company, [])
            )

            table_lines.append(
                "### Wallet Companies Coverage Summary (Excluding BitSafe)"
            )
            table_lines.append(
                f"- **Total Wallet Companies**: {len(wallet_companies_filtered)}"
            )
            table_lines.append(f"- **With Slack**: {wallet_with_slack}")
            table_lines.append(f"- **With Telegram**: {wallet_with_telegram}")
            table_lines.append(f"- **With Calendar**: {wallet_with_calendar}")
            table_lines.append(f"- **With Both Slack + Telegram**: {wallet_with_both}")
            table_lines.append(
                f"- **Missing Slack**: {len(wallet_companies_filtered) - wallet_with_slack}"
            )
            table_lines.append(
                f"- **Missing Telegram**: {len(wallet_companies_filtered) - wallet_with_telegram}"
            )
            table_lines.append("")

        # Show all companies
        table_lines.append("## Complete Company Mapping")
        table_lines.append(
            "| Company | Slack Channel | Telegram Group | Calendar Entries | Wallet Status |"
        )
        table_lines.append(
            "|---------|---------------|----------------|------------------|---------------|"
        )

        for company in sorted_companies:
            slack_name = slack_channels.get(company, "")
            telegram_name = telegram_companies.get(company, "")
            calendar_info = calendar_entries.get(company, [])
            wallet_info = wallet_data.get(company, {})

            # Format calendar entries
            if calendar_info:
                calendar_display = "<br>".join(
                    calendar_info[:2]
                )  # Show first 2 meetings
                if len(calendar_info) > 2:
                    calendar_display += f"<br>... and {len(calendar_info) - 2} more"
            else:
                calendar_display = ""

            # Format wallet information
            wallet_display = ""
            if wallet_info:
                status = wallet_info.get("status", "")
                fund_ownership = wallet_info.get("fund_ownership", "")
                deposit = wallet_info.get("current_deposit", "0")
                paid = wallet_info.get("total_paid", "0")

                wallet_display = (
                    f"{status} ({fund_ownership}) - {deposit} CC / {paid} CC"
                )

            # Clean up names for table display
            slack_display = slack_name if slack_name else ""
            telegram_display = telegram_name if telegram_name else ""

            # Highlight overlaps
            is_overlap = any(
                slack_display == match[1] for match in company_matches.values()
            )
            if is_overlap:
                company_display = f"**{company}** (Overlap)"
            else:
                company_display = company

            table_lines.append(
                f"| {company_display} | {slack_display} | {telegram_display} | {calendar_display} | {wallet_display} |"
            )

        table_lines.append("")
        table_lines.append("## Data Source Notes")
        table_lines.append(
            "- **Slack**: Channel names ending with '-bitsafe', '-cbtc', or '-ibtc'"
        )
        table_lines.append(
            "- **Telegram**: Group names from CRM mapping and export analysis"
        )
        table_lines.append(
            "- **Calendar**: Meeting data from Google Calendar integration"
        )
        table_lines.append(
            "- **Wallet**: Billing wallet addresses and financial status from company agreements"
        )
        table_lines.append(
            f"- **Overlaps**: {len(company_matches)} companies have both Slack and Telegram data"
        )

        return "\n".join(table_lines)

    def save_mapping_table(
        self, table_content: str, output_file: str = "company_mapping_table.md"
    ):
        """Save the mapping table to a file"""
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(table_content)
            print(f"✅ Mapping table saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving table: {e}")

    def generate_csv_mapping_table(self) -> str:
        """Generate CSV format mapping table"""
        print("🔍 Loading company data from all sources...")

        # Load data from all sources
        slack_channels = self.load_slack_channels()
        telegram_groups = self.load_telegram_groups()
        calendar_entries = self.load_calendar_entries()
        wallet_data = self.load_wallet_data()

        # Process Telegram groups to extract company names
        telegram_companies = {}
        for chat_dir, content in telegram_groups.items():
            company_name = self._get_telegram_group_name(chat_dir, content)
            if company_name and self._is_company_name(company_name):
                telegram_companies[company_name] = chat_dir

        # Find company matches using improved normalization
        company_matches = self._find_company_matches(slack_channels, telegram_companies)

        # Combine all company names
        all_companies = set()
        all_companies.update(slack_channels.keys())
        all_companies.update(telegram_companies.keys())
        all_companies.update(calendar_entries.keys())

        # Sort companies alphabetically
        sorted_companies = sorted(all_companies, key=str.lower)

        print(f"📊 Found {len(sorted_companies)} companies across all platforms")
        print(f"   Slack channels: {len(slack_channels)}")
        print(f"   Telegram groups: {len(telegram_groups)}")
        print(f"   Telegram companies: {len(telegram_companies)}")
        print(f"   Calendar entries: {len(calendar_entries)}")
        print(f"   Overlaps (Slack + Telegram): {len(company_matches)}")

        # Generate CSV content
        csv_content = []
        csv_content.append(
            "Company Name,Slack Channel,Telegram Group,Calendar Entries,Wallet Status,Platform Overlap"
        )

        # Add companies with both Slack and Telegram data first (overlaps)
        for normalized_name, (
            slack_display,
            slack_channel,
            telegram_company,
            telegram_group,
        ) in sorted(company_matches.items()):
            calendar_info = calendar_entries.get(slack_display, [])

            # Format calendar entries
            if calendar_info:
                calendar_text = "; ".join(calendar_info[:3])  # Show first 3 entries
                if len(calendar_info) > 3:
                    calendar_text += f"; ... and {len(calendar_info) - 3} more"
            else:
                calendar_text = ""

            # Check if company has wallet data
            wallet_status = "Yes" if slack_display in wallet_data else "No"

            csv_content.append(
                f'"{slack_display}","{slack_channel}","{telegram_group}","{calendar_text}","{wallet_status}","Slack + Telegram"'
            )

        # Add all other companies
        for company in sorted_companies:
            if company in [match[1] for match in company_matches.values()]:
                continue  # Skip companies already added as overlaps

            slack_name = slack_channels.get(company, "")
            telegram_name = telegram_companies.get(company, "")
            calendar_info = calendar_entries.get(company, [])
            wallet_status = "Yes" if company in wallet_data else "No"

            # Determine platform presence
            platforms = []
            if company in slack_channels:
                platforms.append("Slack")
            if company in telegram_companies:
                platforms.append("Telegram")
            if company in calendar_entries:
                platforms.append("Calendar")
            if company in wallet_data:
                platforms.append("Wallet")

            platform_overlap = " + ".join(platforms) if platforms else "None"

            # Format calendar entries
            if calendar_info:
                calendar_text = "; ".join(calendar_info[:3])
                if len(calendar_info) > 3:
                    calendar_text += f"; ... and {len(calendar_info) - 3} more"
            else:
                calendar_text = ""

            csv_content.append(
                f'"{company}","{slack_name}","{telegram_name}","{calendar_text}","{wallet_status}","{platform_overlap}"'
            )

        # Save to CSV file in output directory
        timestamp = datetime.now().strftime("%Y-%m-%d")
        output_file = f"output/company_mapping_table_{timestamp}.csv"

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(csv_content))
            print(f"📁 CSV table saved to: {output_file}")
            return output_file
        except Exception as e:
            print(f"❌ Error saving CSV table: {e}")
            return ""

    def print_mapping_table(self, table_content: str):
        """Print the mapping table to console"""
        print("\n" + "=" * 80)
        print("COMPANY MAPPING TABLE")
        print("=" * 80)

        # Parse and display as a formatted table
        lines = table_content.split("\n")
        for line in lines:
            if line.startswith("|"):
                # Parse table row
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                if len(cells) == 5:
                    company, slack, telegram, calendar, wallet = cells
                    print(
                        f"{company:<25} | {slack:<20} | {telegram:<25} | {calendar:<30} | {wallet}"
                    )
                elif len(cells) == 4:
                    company, slack, telegram, calendar = cells
                    print(f"{company:<25} | {slack:<20} | {telegram:<25} | {calendar}")
            elif line.startswith("#"):
                print(f"\n{line}")
            elif line.strip():
                print(line)

    def run(self):
        """Run the complete mapping table generation"""
        print("🚀 Starting Company Mapping Table Generation...")

        # Generate CSV table
        csv_file = self.generate_csv_mapping_table()

        # Generate markdown table
        table_content = self.generate_mapping_table()

        # Save markdown to file
        self.save_mapping_table(table_content)

        # Print to console
        self.print_mapping_table(table_content)

        print(f"\n✅ Mapping table generation complete!")
        print(f"📁 CSV table saved to: {csv_file}")
        print(f"📁 Markdown table saved to: company_mapping_table.md")


def main():
    """Main function"""
    mapper = CompanyMappingTable()
    mapper.run()


if __name__ == "__main__":
    main()
