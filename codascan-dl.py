#!/usr/bin/env python3
"""
Cantonscan.com party wallet balance scraper with automatic retry functionality
"""

import asyncio
import re
import urllib.parse
from playwright.async_api import async_playwright
import time

async def extract_party_links(page):
    """Extract all party links from the main page"""
    print("🔍 Extracting party links...")
    
    # Wait for page to load completely
    await page.wait_for_timeout(5000)
    
    # Try multiple approaches to find and click the Parties button
    parties_button = None
    
    # Approach 1: Look for exact text
    try:
        parties_button = await page.wait_for_selector('text="Parties (236)"', timeout=5000)
        print("✅ Found Parties button with exact text")
    except:
        pass
    
    # Approach 2: Look for button with "Parties" text
    if not parties_button:
        try:
            parties_button = await page.wait_for_selector('button:has-text("Parties")', timeout=5000)
            print("✅ Found Parties button with 'Parties' text")
        except:
            pass
    
    # Approach 3: Look for any element with "Parties" text
    if not parties_button:
        try:
            parties_button = await page.wait_for_selector('*:has-text("Parties")', timeout=5000)
            print("✅ Found element with 'Parties' text")
        except:
            pass
    
    # Approach 4: Look for navigation or menu items
    if not parties_button:
        try:
            # Try to find navigation links
            nav_links = await page.query_selector_all('nav a, .nav a, [role="navigation"] a')
            for link in nav_links:
                try:
                    text = await link.text_content()
                    if 'parties' in text.lower():
                        parties_button = link
                        print(f"✅ Found navigation link: {text}")
                        break
                except:
                    continue
        except:
            pass
    
    # Approach 5: Try to find any clickable element with "236" in it
    if not parties_button:
        try:
            elements_with_236 = await page.query_selector_all('*')
            for elem in elements_with_236[:50]:  # Check first 50 elements
                try:
                    text = await elem.text_content()
                    if text and '236' in text and ('parties' in text.lower() or 'party' in text.lower()):
                        parties_button = elem
                        print(f"✅ Found element with '236': {text[:50]}...")
                        break
                except:
                    continue
        except:
            pass
    
    # Click the button if found
    if parties_button:
        try:
            await parties_button.click()
            print("✅ Clicked on Parties button")
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"⚠️ Could not click button: {e}")
    else:
        print("⚠️ Could not find Parties button, trying to extract links directly...")
    
    # Scroll to load all parties
    print("📜 Scrolling to load all parties...")
    for i in range(10):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
    
    # Extract all party links
    party_links = await page.evaluate("""
        () => {
            const links = Array.from(document.querySelectorAll('a[href*="/party/"]'));
            return links.map(link => link.href).filter(href => href.includes('/party/'));
        }
    """)
    
    # If no party links found, try alternative approach
    if not party_links:
        print("🔍 No party links found, trying alternative extraction...")
        
        # Try to find any links that might be party links
        all_links = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a'));
                return links.map(link => ({href: link.href, text: link.textContent}));
            }
        """)
        
        # Filter for potential party links
        for link_info in all_links:
            if '/party/' in link_info['href']:
                party_links.append(link_info['href'])
    
    print(f"✅ Found {len(party_links)} party links")
    return party_links

def extract_party_name_from_url(url):
    """Extract party name from URL"""
    match = re.search(r'/party/([^%]+)', url)
    if match:
        return match.group(1)
    return "unknown"

def extract_party_id_from_url(url):
    """Extract and decode party ID from URL"""
    # Extract the party ID part from the URL
    # URL format: https://www.cantonscan.com/party/sendit%3A%3A1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
    try:
        party_part = url.split('/party/')[-1]
        # Decode URL encoding (%3A becomes :)
        decoded_part = urllib.parse.unquote(party_part)
        # Return the full party ID (party_name::hash)
        return decoded_part
    except:
        return "unknown"

def extract_balance_from_html(html_content, text_content):
    """Extract balance from HTML content"""
    # Look for balance patterns in the text content
    balance_patterns = [
        r'Wallet Balance([\d,]+\.\d+)',
        r'Balance([\d,]+\.\d+)',
        r'([\d,]+\.\d+)\s*At Round',
        r'([\d,]+\.\d+)\s*Effective Time'
    ]
    
    for pattern in balance_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        for match in matches:
            balance = match.replace(',', '')
            if re.match(r'^\d+\.\d+$', balance):
                if not re.match(r'^20\d{2}$', balance.split('.')[0]):
                    return balance
    
    return "0.00"

async def process_single_page(url, browser, timeout=30000, retry_mode=False):
    """Process a single page with configurable timeout and retry mode"""
    page = await browser.new_page()
    
    try:
        # Use longer timeout for retry mode
        actual_timeout = 60000 if retry_mode else timeout
        await page.goto(url, wait_until="domcontentloaded", timeout=actual_timeout)
        
        # Wait for content to load (longer wait for retry mode)
        wait_time = 8000 if retry_mode else 3000
        await page.wait_for_timeout(wait_time)
        
        # Get page content
        html_content = await page.content()
        text_content = await page.text_content('body')
        
        # Extract party name
        party_name = extract_party_name_from_url(url)
        
        # Extract balance
        balance = extract_balance_from_html(html_content, text_content)
        
        status_icon = "🔄" if retry_mode else "✅"
        print(f"   {status_icon} {party_name}: {balance}")
        
        return {
            'party': party_name,
            'balance': balance,
            'url': url
        }
        
    except Exception as e:
        party_name = extract_party_name_from_url(url)
        error_msg = f"Error: {str(e)}"
        status_icon = "❌" if retry_mode else "⚠️"
        print(f"   {status_icon} {party_name}: {error_msg}")
        return {
            'party': party_name,
            'balance': error_msg,
            'url': url
        }
    finally:
        await page.close()

async def process_batch(urls, browser, batch_num, total_batches, batch_size=50, retry_mode=False):
    """Process a batch of URLs"""
    print(f"\n📦 Processing batch {batch_num}/{total_batches}")
    
    # Show which parties are being processed
    for url in urls:
        party_name = extract_party_name_from_url(url)
        print(f"   🔍 Processing: {party_name}")
    
    # Process all URLs in the batch concurrently
    tasks = [process_single_page(url, browser, retry_mode=retry_mode) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            party_name = extract_party_name_from_url(urls[i])
            processed_results.append({
                'party': party_name,
                'balance': f"Error: {str(result)}",
                'url': urls[i]
            })
        else:
            processed_results.append(result)
    
    return processed_results

async def retry_failed_entries(failed_entries, browser):
    """Retry failed entries with longer timeouts and individual processing"""
    print(f"\n🔄 Retrying {len(failed_entries)} failed entries with extended timeouts...")
    
    results = []
    
    for i, entry in enumerate(failed_entries, 1):
        print(f"\n🔍 Retrying {i}/{len(failed_entries)}: {entry['party']}")
        
        result = await process_single_page(entry['url'], browser, retry_mode=True)
        results.append(result)
        
        # Small delay between retry requests
        await asyncio.sleep(2)
    
    return results

async def main():
    """Main function with automatic retry functionality"""
    print("🚀 Starting Cantonscan.com party wallet balance scraper...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Navigate to the main page
        page = await browser.new_page()
        await page.goto("https://www.cantonscan.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Extract party links
        party_links = await extract_party_links(page)
        await page.close()
        
        if not party_links:
            print("❌ No party links found. Exiting.")
            await browser.close()
            return
        
        print(f"📊 Found {len(party_links)} parties to process")
        
        # Process in batches
        batch_size = 50
        total_batches = (len(party_links) + batch_size - 1) // batch_size
        all_results = []
        
        for i in range(0, len(party_links), batch_size):
            batch_urls = party_links[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            results = await process_batch(batch_urls, browser, batch_num, total_batches, batch_size)
            all_results.extend(results)
        
        # Identify failed entries
        failed_entries = [result for result in all_results if result['balance'].startswith('Error:')]
        
        if failed_entries:
            print(f"\n⚠️ Found {len(failed_entries)} failed entries, attempting retry...")
            
            # Retry failed entries
            retry_results = await retry_failed_entries(failed_entries, browser)
            
            # Replace failed entries with retry results
            for i, result in enumerate(all_results):
                if result['balance'].startswith('Error:'):
                    # Find corresponding retry result
                    for retry_result in retry_results:
                        if retry_result['party'] == result['party']:
                            all_results[i] = retry_result
                            break
        
        await browser.close()
        
        # Write results to file
        print(f"\n💾 Writing results to codascan_balances.txt...")
        with open("codascan_balances.txt", "w") as f:
            f.write("Party Name\tParty ID\tBalance\tURL\n")
            for result in all_results:
                # Skip error entries
                if result['balance'].startswith('Error:') or result['balance'] == 'Not found':
                    continue
                # Extract partyid from URL
                partyid = extract_party_id_from_url(result['url'])
                f.write(f"{result['party']}\t{partyid}\t{result['balance']}\t{result['url']}\n")
        
        # Write errors to separate error log
        print(f"📝 Writing errors to codascan_errors.log...")
        with open("codascan_errors.log", "w") as error_f:
            error_f.write("Error Log - Cantonscan Scraping\n")
            error_f.write("=" * 50 + "\n\n")
            for result in all_results:
                if result['balance'].startswith('Error:') or result['balance'] == 'Not found':
                    error_f.write(f"Party: {result['party']}\n")
                    error_f.write(f"URL: {result['url']}\n")
                    error_f.write(f"Error: {result['balance']}\n")
                    error_f.write("-" * 30 + "\n")
        
        # Final statistics
        successful = sum(1 for r in all_results if not r['balance'].startswith('Error:'))
        failed = len(all_results) - successful
        
        print(f"✅ Results saved to codascan_balances.txt")
        print(f"📊 Processed {len(all_results)} parties")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📄 Errors saved to codascan_errors.log")

if __name__ == "__main__":
    asyncio.run(main())
