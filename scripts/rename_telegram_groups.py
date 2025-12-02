#!/usr/bin/env python3
"""
Rename Telegram Groups - Remove iBTC Branding

Renames Telegram groups to remove "iBTC" references and standardize naming.
"""

import asyncio
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import EditTitleRequest
from telethon.tl.functions.messages import EditChatTitleRequest
from telethon.tl.types import Channel, Chat

load_dotenv()

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

# Rename mapping (old_name -> new_name)
RENAME_MAP = {
    "Allnodes <> BitSafe (iBTC, CBTC)": "Allnodes <> BitSafe (CBTC)",
    "AmberGroup <> BitSafe (iBTC, CBTC)": "AmberGroup <> BitSafe (CBTC)",
    "BitSafe (iBTC) <> Wave Digital Assets": "BitSafe (CBTC) <> Wave Digital Assets",
    "BitSafe (iBTC, CBTC) <> Cumberland": "BitSafe (CBTC) <> Cumberland",
    "BitSafe (CBTC, iBTC) <> Animoca - New": "BitSafe (CBTC) <> Animoca",
    "Boosty <> BitSafe (iBTC, CBTC)": "Boosty <> BitSafe (CBTC)",
    "Bosonic <> iBTC": "Bosonic <> BitSafe (CBTC)",
    "ByBit Institutional <> iBTC": "ByBit Institutional <> BitSafe (CBTC)",
    "Chainlink <> BitSafe (iBTC, CBTC)": "Chainlink <> BitSafe (CBTC)",
    "Coinstore <> iBTC": "Coinstore <> BitSafe (CBTC)",
    "Comma3 Ventures <> BitSafe (iBTC, CBTC)": "Comma3 Ventures <> BitSafe (CBTC)",
    "Copper <> BitSafe (iBTC, CBTC)": "Copper <> BitSafe (CBTC)",
    "DFNS <> BitSafe (iBTC, CBTC)": "DFNS <> BitSafe (CBTC)",
    "Dark Forest <> iBTC": "Dark Forest <> BitSafe (CBTC)",
    "Dewhales <> BitSafe (CBTC, iBTC)": "Dewhales <> BitSafe (CBTC)",
    "Edge Capital <> iBTC": "Edge Capital <> BitSafe (CBTC)",
    "Ergonia <> BitSafe (iBTC, CBTC)": "Ergonia <> BitSafe (CBTC)",
    "Fireblocks Sales <> BitSafe (CBTC, iBTC)": "Fireblocks Sales <> BitSafe (CBTC)",
    "Five Bells <> iBTC": "Five Bells <> BitSafe (CBTC)",
    "Fordefi <> BitSafe (CBTC, iBTC)": "Fordefi <> BitSafe (CBTC)",
    "Forteus | iBTC": "Forteus <> BitSafe (CBTC)",
    "GoQuant <> BitSafe (iBTC, CBTC)": "GoQuant <> BitSafe (CBTC)",
    "Hashnote <> BitSafe (CBTC, iBTC)": "Hashnote <> BitSafe (CBTC)",
    "iBTC / Psalion": "BitSafe (CBTC) <> Psalion",
    "K3 Labs <> BitSafe (iBTC, CBTC)": "K3 Labs <> BitSafe (CBTC)",
    "Komainu <> iBTC": "Komainu <> BitSafe (CBTC)",
    "KuCoin <> iBTC": "KuCoin <> BitSafe (CBTC)",
    "LTP <> BitSafe (iBTC, CBTC)": "LTP <> BitSafe (CBTC)",
    "Lagoon <> BitSafe (CBTC, iBTC)": "Lagoon <> BitSafe (CBTC)",
    "LayerZero <> BitSafe (iBTC, CBTC)": "LayerZero <> BitSafe (CBTC)",
    "Meria <> BitSafe (iBTC, CBTC)": "Meria <> BitSafe (CBTC)",
    "Metalpha <> iBTC": "Metalpha <> BitSafe (CBTC)",
    "P2P.org <> BitSafe (iBTC, CBTC) - New": "P2P.org <> BitSafe (CBTC)",
    "Pattern Research <> BitSafe (CBTC, iBTC)": "Pattern Research <> BitSafe (CBTC)",
    "Pier Two <> BitSafe (iBTC, CBTC)": "Pier Two <> BitSafe (CBTC)",
    "Prototech <> BitSafe (iBTC, CBTC)": "Prototech <> BitSafe (CBTC)",
    "Pyth <> iBTC (new)": "Pyth <> BitSafe (CBTC)",
    "Republic <> BitSafe (iBTC, CBTC)": "Republic <> BitSafe (CBTC)",
    "Round13 <> BitSafe (iBTC)": "Round13 <> BitSafe (CBTC)",
    "Samara <> BitSafe (iBTC)": "Samara <> BitSafe (CBTC)",
    "SmartBitcoinLabs <> BitSafe (CBTC, iBTC)": "SmartBitcoinLabs <> BitSafe (CBTC)",
    "Term Structure <> BitSafe (iBTC, CBTC)": "Term Structure <> BitSafe (CBTC)",
    "Tintash <> BitSafe (iBTC, CBTC)": "Tintash <> BitSafe (CBTC)",
    "Valos <> iBTC": "Valos <> BitSafe (CBTC)",
    "VanEck <> BitSafe (CBTC, iBTC)": "VanEck <> BitSafe (CBTC)",
    "Vaults.fyi <> iBTC": "Vaults.fyi <> BitSafe (CBTC)",
    "Veda <> BitSafe (CBTC, iBTC)": "Veda <> BitSafe (CBTC)",
}


async def rename_groups():
    client = TelegramClient("anon", api_id, api_hash)
    await client.start(phone)

    print("🔄 Telegram Group Rename Tool")
    print("=" * 70)
    print(f"Groups to rename: {len(RENAME_MAP)}")
    print("=" * 70)
    print()

    success = []
    failed = []
    not_found = []

    # Get all dialogs to find our target groups
    async for dialog in client.iter_dialogs():
        if dialog.title in RENAME_MAP:
            old_name = dialog.title
            new_name = RENAME_MAP[old_name]
            entity = dialog.entity

            try:
                # Rename based on type
                if isinstance(entity, Channel):
                    await client(EditTitleRequest(channel=entity, title=new_name))
                elif isinstance(entity, Chat):
                    await client(
                        EditChatTitleRequest(chat_id=entity.id, title=new_name)
                    )
                else:
                    failed.append((old_name, "Unsupported chat type"))
                    print(f"❌ FAILED: {old_name}")
                    print(f"   Reason: Unsupported chat type")
                    continue

                success.append((old_name, new_name))
                print(f"✅ RENAMED: {old_name}")
                print(f"        → {new_name}")

            except Exception as e:
                failed.append((old_name, str(e)))
                print(f"❌ FAILED: {old_name}")
                print(f"   Error: {e}")

            await asyncio.sleep(0.5)  # Rate limiting

    # Check which groups weren't found
    found_names = [name for name, _ in success] + [name for name, _ in failed]
    not_found = [name for name in RENAME_MAP.keys() if name not in found_names]

    # Summary
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully renamed: {len(success)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"⚠️  Not found: {len(not_found)}")
    print()

    if failed:
        print("Failed groups:")
        for name, error in failed:
            print(f"  ❌ {name}")
            print(f"     {error[:80]}")

    if not_found:
        print()
        print("Not found (may have been renamed already or different name):")
        for name in not_found[:10]:
            print(f"  ⚠️  {name}")
        if len(not_found) > 10:
            print(f"  ... and {len(not_found)-10} more")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(rename_groups())
