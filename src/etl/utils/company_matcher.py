#!/usr/bin/env python3
"""
Enhanced Company Matching Utilities
Provides improved fuzzy matching and name normalization for better data coverage
"""

import re
import string
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple


class CompanyMatcher:
    """Enhanced company matching with fuzzy logic and name normalization"""

    def __init__(self):
        # Common suffixes to remove for better matching
        self.company_suffixes = [
            "inc",
            "llc",
            "corp",
            "ltd",
            "limited",
            "company",
            "co",
            "minter",
            "mainnet",
            "validator",
            "canton",
            "wallet",
            "node",
            "bitsafe",
            "safe",
            "protocol",
            "labs",
            "tech",
            "technologies",
            "systems",
            "solutions",
            "services",
            "group",
            "holdings",
        ]

        # Common prefixes to remove
        self.company_prefixes = [
            "the",
            "a",
            "an",
            "new",
            "advanced",
            "global",
            "international",
        ]

        # Common separators to normalize
        self.separators = ["-", "_", ".", " ", "+", "&", "and"]

    def normalize_name(self, name: str) -> str:
        """Normalize company name for better matching"""
        if not name:
            return ""

        # Convert to lowercase
        normalized = name.lower().strip()

        # Remove common prefixes
        for prefix in self.company_prefixes:
            if normalized.startswith(prefix + " "):
                normalized = normalized[len(prefix) + 1 :]

        # Remove common suffixes
        for suffix in self.company_suffixes:
            if normalized.endswith(" " + suffix):
                normalized = normalized[: -len(suffix) - 1]
            elif normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]

        # Normalize separators to hyphens
        for sep in self.separators:
            normalized = normalized.replace(sep, "-")

        # Remove multiple consecutive hyphens
        normalized = re.sub(r"-+", "-", normalized)

        # Remove leading/trailing hyphens
        normalized = normalized.strip("-")

        return normalized

    def generate_name_variants(self, name: str) -> List[str]:
        """Generate various name variants for matching"""
        variants = set()

        if not name:
            return list(variants)

        # Original name
        variants.add(name)
        variants.add(name.lower())

        # Normalized name
        normalized = self.normalize_name(name)
        variants.add(normalized)

        # Remove separators completely
        no_sep = re.sub(r"[-_\s.]+", "", name.lower())
        variants.add(no_sep)

        # Remove common suffixes and prefixes
        for suffix in self.company_suffixes:
            if name.lower().endswith(suffix):
                base = name.lower()[: -len(suffix)].strip()
                variants.add(base)
                variants.add(self.normalize_name(base))

        # Add variants with different separators
        base_name = self.normalize_name(name)
        for sep in ["-", "_", " ", "."]:
            variants.add(base_name.replace("-", sep))

        # Add acronym version (first letters of words) - only for longer names
        words = re.split(r"[-_\s.]+", name)
        if len(words) > 1 and len(name) > 6:  # Only create acronyms for longer names
            acronym = "".join(word[0] for word in words if word)
            if len(acronym) >= 3:  # Only add acronyms with 3+ characters
                variants.add(acronym.lower())

        # Filter out very short or generic terms
        filtered_variants = []
        generic_terms = {
            "gm",
            "om",
            "em",
            "al",
            "tr",
            "ac",
            "sc",
            "rm",
            "am",
            "im",
            "pt",
            "ui",
            "bc",
            "fm",
            "tm",
            "a0",
            "ig",
        }

        for v in variants:
            if v and len(v) > 2 and v not in generic_terms:
                filtered_variants.append(v)

        return filtered_variants

    def fuzzy_match(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
        """Check if two names are similar using fuzzy matching"""
        if not name1 or not name2:
            return False

        # Direct match
        if name1.lower() == name2.lower():
            return True

        # Normalized match
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        if norm1 == norm2:
            return True

        # Fuzzy similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        if similarity >= threshold:
            return True

        # Check if one name contains the other (but only if it's a significant portion)
        # Require at least 6 characters and avoid common suffixes/prefixes
        if len(norm1) >= 6 and len(norm2) >= 6:
            # Avoid matching on common suffixes like "-bit", "-safe", etc.
            common_suffixes = [
                "-bit",
                "-safe",
                "-minter",
                "-mainnet",
                "-bitsafe",
                "bit",
                "safe",
            ]
            has_common_suffix = any(
                suffix in norm1 or suffix in norm2 for suffix in common_suffixes
            )

            if not has_common_suffix and (norm1 in norm2 or norm2 in norm1):
                return True

        return False

    def match_company_to_channel(
        self,
        company_name: str,
        company_info: Dict,
        channel_name: str,
        channel_type: str = "slack",
    ) -> bool:
        """Enhanced matching between company and channel/chat"""
        if not company_name or not channel_name:
            return False

        # For Telegram, use specialized matching
        if channel_type == "telegram":
            return self._match_telegram_chat(company_name, company_info, channel_name)

        # For Calendar, use specialized matching
        if channel_type == "calendar":
            return self._match_calendar_meeting(
                company_name, company_info, channel_name
            )

        # For HubSpot, use specialized matching
        if channel_type == "hubspot":
            return self._match_hubspot_company(company_name, company_info, channel_name)

        # Generate variants for both names
        company_variants = self.generate_name_variants(company_name)
        channel_variants = self.generate_name_variants(channel_name)

        # Check direct matches
        for company_var in company_variants:
            for channel_var in channel_variants:
                if self.fuzzy_match(company_var, channel_var):
                    return True

        # Check against base company
        if company_info.get("base_company"):
            base_variants = self.generate_name_variants(company_info["base_company"])
            for base_var in base_variants:
                for channel_var in channel_variants:
                    if self.fuzzy_match(base_var, channel_var):
                        return True

        # Check against variants field
        if company_info.get("variant_type"):
            variants_str = company_info["variant_type"]
            if variants_str:
                # Split variants by comma and process each
                variants = [v.strip() for v in variants_str.split(",")]
                for variant in variants:
                    variant_variants = self.generate_name_variants(variant)
                    for var_var in variant_variants:
                        for channel_var in channel_variants:
                            if self.fuzzy_match(var_var, channel_var):
                                return True

        # Check against slack_groups or telegram_groups
        groups_field = f"{channel_type}_groups"
        if company_info.get(groups_field):
            groups_str = company_info[groups_field]
            if groups_str:
                groups = [g.strip() for g in groups_str.split(",")]
                for group in groups:
                    group_variants = self.generate_name_variants(group)
                    for group_var in group_variants:
                        for channel_var in channel_variants:
                            if self.fuzzy_match(group_var, channel_var):
                                return True

        # Special handling for bitsafe channels
        if channel_name.lower().endswith("-bitsafe"):
            bitsafe_base = channel_name.lower().replace("-bitsafe", "")
            bitsafe_variants = self.generate_name_variants(bitsafe_base)

            for company_var in company_variants:
                for bitsafe_var in bitsafe_variants:
                    if self.fuzzy_match(company_var, bitsafe_var):
                        return True

            # Check against base company
            if company_info.get("base_company"):
                base_variants = self.generate_name_variants(
                    company_info["base_company"]
                )
                for base_var in base_variants:
                    for bitsafe_var in bitsafe_variants:
                        if self.fuzzy_match(base_var, bitsafe_var):
                            return True

        return False

    def find_best_matches(
        self,
        company_name: str,
        company_info: Dict,
        channels: Dict[str, Dict],
        channel_type: str = "slack",
    ) -> List[Tuple[str, float]]:
        """Find best matching channels for a company with confidence scores"""
        matches = []

        for channel_id, channel_data in channels.items():
            # Get channel name based on channel type
            if channel_type == "telegram":
                channel_name = channel_data.get("chat_name", "")
            else:  # slack, calendar, etc.
                channel_name = channel_data.get("name", "")

            if self.match_company_to_channel(
                company_name, company_info, channel_name, channel_type
            ):
                # Calculate confidence score
                confidence = self.calculate_confidence(
                    company_name, company_info, channel_name, channel_type
                )
                matches.append((channel_id, confidence))

        # Sort by confidence score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def calculate_confidence(
        self,
        company_name: str,
        company_info: Dict,
        channel_name: str,
        channel_type: str = "slack",
    ) -> float:
        """Calculate confidence score for a match"""
        if not company_name or not channel_name:
            return 0.0

        # Generate variants
        company_variants = self.generate_name_variants(company_name)
        channel_variants = self.generate_name_variants(channel_name)

        max_confidence = 0.0

        # Check direct matches (highest confidence)
        for company_var in company_variants:
            for channel_var in channel_variants:
                if company_var == channel_var:
                    return 1.0
                elif company_var in channel_var or channel_var in company_var:
                    max_confidence = max(max_confidence, 0.9)

        # Check fuzzy matches
        for company_var in company_variants:
            for channel_var in channel_variants:
                similarity = SequenceMatcher(None, company_var, channel_var).ratio()
                if similarity > 0.8:
                    max_confidence = max(max_confidence, similarity)

        # Check against base company
        if company_info.get("base_company"):
            base_variants = self.generate_name_variants(company_info["base_company"])
            for base_var in base_variants:
                for channel_var in channel_variants:
                    if base_var == channel_var:
                        return 0.95
                    elif base_var in channel_var or channel_var in base_var:
                        max_confidence = max(max_confidence, 0.85)

        # Check against groups field
        groups_field = f"{channel_type}_groups"
        if company_info.get(groups_field):
            groups_str = company_info[groups_field]
            if groups_str:
                groups = [g.strip() for g in groups_str.split(",")]
                for group in groups:
                    group_variants = self.generate_name_variants(group)
                    for group_var in group_variants:
                        for channel_var in channel_variants:
                            if group_var == channel_var:
                                return 0.9
                            elif group_var in channel_var or channel_var in group_var:
                                max_confidence = max(max_confidence, 0.8)

        return max_confidence

    def _match_telegram_chat(
        self, company_name: str, company_info: Dict, chat_name: str
    ) -> bool:
        """Special matching logic for Telegram chats"""
        if not company_name or not chat_name:
            return False

        # Extract potential company names from chat name
        # Chat names like "System-Shirin - ProBit Global-telegram" should match "ProBit Global"
        chat_parts = chat_name.replace("-telegram", "").split("-")

        # Try to find company name in chat parts
        for part in chat_parts:
            part = part.strip()
            if len(part) < 3:  # Skip very short parts
                continue

            # Generate variants for this part
            part_variants = self.generate_name_variants(part)
            company_variants = self.generate_name_variants(company_name)

            # Check if any variant matches
            for company_var in company_variants:
                for part_var in part_variants:
                    if self.fuzzy_match(company_var, part_var):
                        return True

            # Check against base company
            if company_info.get("base_company"):
                base_variants = self.generate_name_variants(
                    company_info["base_company"]
                )
                for base_var in base_variants:
                    for part_var in part_variants:
                        if self.fuzzy_match(base_var, part_var):
                            return True

        # Also check the full chat name (without -telegram suffix)
        full_chat_name = chat_name.replace("-telegram", "").strip()
        if full_chat_name:
            chat_variants = self.generate_name_variants(full_chat_name)
            company_variants = self.generate_name_variants(company_name)

            for company_var in company_variants:
                for chat_var in chat_variants:
                    if self.fuzzy_match(company_var, chat_var):
                        return True

        return False

    def _match_calendar_meeting(
        self, company_name: str, company_info: Dict, meeting_text: str
    ) -> bool:
        """Specialized matching logic for calendar meetings"""
        if not company_name or not meeting_text:
            return False

        meeting_text_lower = meeting_text.lower()

        # 1. Check company name variants in meeting text
        company_variants = self.generate_name_variants(company_name)
        for variant in company_variants:
            if variant.lower() in meeting_text_lower:
                return True

        # 2. Check base company name
        if company_info.get("base_company"):
            base_variants = self.generate_name_variants(company_info["base_company"])
            for variant in base_variants:
                if variant.lower() in meeting_text_lower:
                    return True

        # 3. Check calendar domain in meeting text
        calendar_domain = company_info.get("calendar_domain", "")
        if calendar_domain:
            domain_variants = self.generate_name_variants(calendar_domain)
            for variant in domain_variants:
                if variant.lower() in meeting_text_lower:
                    return True

            # Also check for email patterns with this domain
            if f"@{calendar_domain}" in meeting_text_lower:
                return True

        # 4. Check variants field
        if company_info.get("variant_type"):
            variants_str = company_info["variant_type"]
            if variants_str:
                variants = [v.strip() for v in variants_str.split(",")]
                for variant in variants:
                    variant_variants = self.generate_name_variants(variant)
                    for var in variant_variants:
                        if var.lower() in meeting_text_lower:
                            return True

        # 5. Check for common meeting patterns
        # Look for company name in common meeting title patterns
        common_patterns = [
            f"meeting with {company_name.lower()}",
            f"call with {company_name.lower()}",
            f"{company_name.lower()} meeting",
            f"{company_name.lower()} call",
            f"discussion with {company_name.lower()}",
        ]

        for pattern in common_patterns:
            if pattern in meeting_text_lower:
                return True

        # 6. Enhanced pattern matching for calendar meetings
        company_name_clean = company_name.replace("-", "").replace("_", "").lower()

        # Only match if the company name appears as a complete word or with common suffixes
        import re

        # Basic word patterns
        word_patterns = [
            rf"\b{re.escape(company_name_clean)}\b",  # Complete word
            rf"{re.escape(company_name_clean)}\.com",  # Domain
            rf"{re.escape(company_name_clean)}\s+(meeting|call|discussion|session)",  # Meeting patterns
            rf"(meeting|call|discussion|session)\s+with\s+{re.escape(company_name_clean)}",  # Meeting with patterns
        ]

        for pattern in word_patterns:
            if re.search(pattern, meeting_text_lower):
                return True

        # 7. Enhanced business meeting patterns
        business_patterns = [
            # Company name in various business contexts
            rf"{re.escape(company_name_clean)}\s+(advisory|working|group|sprint|session|call|meeting|demo|presentation)",
            rf"(advisory|working|group|sprint|session|call|meeting|demo|presentation)\s+.*{re.escape(company_name_clean)}",
            rf"{re.escape(company_name_clean)}\s+(tokenomics|strategy|planning|review|sync|standup)",
            rf"(tokenomics|strategy|planning|review|sync|standup).*{re.escape(company_name_clean)}",
            # Company name with common business prefixes/suffixes
            rf"{re.escape(company_name_clean)}\s+(inc|llc|corp|ltd|limited|company|co)",
            rf"(inc|llc|corp|ltd|limited|company|co)\s+{re.escape(company_name_clean)}",
        ]

        for pattern in business_patterns:
            if re.search(pattern, meeting_text_lower):
                return True

        # 8. Partial matching for shorter company names (3+ characters)
        if len(company_name_clean) >= 3:
            # Look for company name as part of larger words in business context
            partial_patterns = [
                rf"\b\w*{re.escape(company_name_clean)}\w*\b",  # Company name as part of word
                rf"{re.escape(company_name_clean)}\w*",  # Company name at start of word
                rf"\w*{re.escape(company_name_clean)}",  # Company name at end of word
            ]

            for pattern in partial_patterns:
                if re.search(pattern, meeting_text_lower):
                    return True

        return False

    def _match_hubspot_company(
        self, company_name: str, company_info: Dict, hubspot_company: str
    ) -> bool:
        """Specialized matching logic for HubSpot company names"""
        if not company_name or not hubspot_company:
            return False

        hubspot_company_lower = hubspot_company.lower()

        # 1. Check company name variants in HubSpot company name
        company_variants = self.generate_name_variants(company_name)
        for variant in company_variants:
            if variant.lower() in hubspot_company_lower:
                return True

        # 2. Check base company name
        if company_info.get("base_company"):
            base_variants = self.generate_name_variants(company_info["base_company"])
            for variant in base_variants:
                if variant.lower() in hubspot_company_lower:
                    return True

        # 3. Check calendar domain in HubSpot company name
        calendar_domain = company_info.get("calendar_domain", "")
        if calendar_domain:
            domain_variants = self.generate_name_variants(calendar_domain)
            for variant in domain_variants:
                if variant.lower() in hubspot_company_lower:
                    return True

        # 4. Check variants field
        if company_info.get("variant_type"):
            variants_str = company_info["variant_type"]
            if variants_str:
                variants = [v.strip() for v in variants_str.split(",")]
                for variant in variants:
                    variant_variants = self.generate_name_variants(variant)
                    for var in variant_variants:
                        if var.lower() in hubspot_company_lower:
                            return True

        # 5. Enhanced fuzzy matching for HubSpot company names
        # HubSpot often has variations like "Company Inc.", "Company LLC", etc.
        company_name_clean = (
            company_name.replace("-", "").replace("_", "").replace(" ", "").lower()
        )
        hubspot_clean = (
            hubspot_company_lower.replace("inc", "")
            .replace("llc", "")
            .replace("corp", "")
            .replace("ltd", "")
            .replace("limited", "")
            .replace("company", "")
            .replace("co", "")
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )

        # Direct match after cleaning
        if company_name_clean == hubspot_clean:
            return True

        # Partial match
        if company_name_clean in hubspot_clean or hubspot_clean in company_name_clean:
            return True

        # 6. Check for common business suffixes and prefixes
        business_suffixes = [
            "inc",
            "llc",
            "corp",
            "ltd",
            "limited",
            "company",
            "co",
            "group",
            "holdings",
            "enterprises",
        ]
        business_prefixes = [
            "the",
            "a",
            "an",
            "new",
            "advanced",
            "global",
            "international",
        ]

        # Remove business suffixes from both names and compare
        for suffix in business_suffixes:
            if hubspot_company_lower.endswith(suffix):
                hubspot_no_suffix = hubspot_company_lower[: -len(suffix)].strip()
                if (
                    company_name_clean in hubspot_no_suffix
                    or hubspot_no_suffix in company_name_clean
                ):
                    return True

        # 7. Check against base company with business suffixes
        if company_info.get("base_company"):
            base_company_clean = (
                company_info["base_company"]
                .replace("-", "")
                .replace("_", "")
                .replace(" ", "")
                .lower()
            )
            for suffix in business_suffixes:
                if hubspot_company_lower.endswith(suffix):
                    hubspot_no_suffix = hubspot_company_lower[: -len(suffix)].strip()
                    if (
                        base_company_clean in hubspot_no_suffix
                        or hubspot_no_suffix in base_company_clean
                    ):
                        return True

        return False

    def _match_email_domain_to_company(
        self, company_name: str, company_info: Dict, domain: str
    ) -> bool:
        """Match email domain to company using various strategies"""
        if not domain:
            return False

        domain_lower = domain.lower()

        # 1. Direct domain match
        if (
            company_info.get("calendar_domain")
            and domain_lower == company_info["calendar_domain"].lower()
        ):
            return True

        # 2. Company name in domain
        company_name_clean = (
            company_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        )
        domain_clean = (
            domain_lower.replace(".com", "")
            .replace(".org", "")
            .replace(".net", "")
            .replace(".io", "")
        )

        if company_name_clean in domain_clean or domain_clean in company_name_clean:
            return True

        # 3. Check against base company
        if company_info.get("base_company"):
            base_company_clean = (
                company_info["base_company"]
                .lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
            )
            if base_company_clean in domain_clean or domain_clean in base_company_clean:
                return True

        # 4. Check against variants
        if company_info.get("variant_type"):
            variants_str = company_info["variant_type"]
            if variants_str:
                variants = [v.strip() for v in variants_str.split(",")]
                for variant in variants:
                    variant_clean = (
                        variant.lower()
                        .replace(" ", "")
                        .replace("-", "")
                        .replace("_", "")
                    )
                    if variant_clean in domain_clean or domain_clean in variant_clean:
                        return True

        # 5. Fuzzy domain matching for partial matches
        if len(domain_clean) > 3 and len(company_name_clean) > 3:
            # Check if significant portion of company name is in domain
            if len(company_name_clean) >= 4:
                for i in range(len(company_name_clean) - 3):
                    substring = company_name_clean[i : i + 4]
                    if substring in domain_clean:
                        return True

        return False
