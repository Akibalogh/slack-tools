#!/usr/bin/env python3
"""
Cantonscan.com party wallet balance scraper with automatic retry functionality
"""

import asyncio
from playwright.async_api import async_playwright
import re
import urllib.parse
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('codascan_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run():
    query_hash = "1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2"
    base_url = f"https://cantonscan.com/search/{query_hash}"
    TEST_MODE = False  # Set to False to process all URLs

    async with async_playwright() as p:
        # Launch browser with performance optimizations
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-gpu',  # Disable GPU hardware acceleration
                '--disable-dev-shm-usage',  # Disable /dev/shm usage
                '--disable-web-security',  # Disable web security for faster loading
                '--disable-features=VizDisplayCompositor',  # Disable display compositor
                '--disable-extensions',  # Disable extensions
                '--disable-plugins',  # Disable plugins
                '--disable-images',  # Disable image loading
                # '--disable-javascript',  # Keep JavaScript enabled for dynamic content
                '--disable-background-timer-throttling',  # Disable background timer throttling
                '--disable-backgrounding-occluded-windows',  # Disable backgrounding
                '--disable-renderer-backgrounding',  # Disable renderer backgrounding
                '--disable-background-networking',  # Disable background networking
                '--disable-default-apps',  # Disable default apps
                '--disable-sync',  # Disable sync
                '--disable-translate',  # Disable translate
                '--hide-scrollbars',  # Hide scrollbars
                '--mute-audio',  # Mute audio
                '--no-first-run',  # Skip first run
                '--no-sandbox',  # Disable sandbox (use with caution)
                '--disable-setuid-sandbox',  # Disable setuid sandbox
                # '--single-process',  # Use single process (reduces memory usage) - disabled due to stability issues
                '--memory-pressure-off',  # Turn off memory pressure
                '--max_old_space_size=4096',  # Limit memory usage
            ]
        )
        page = await browser.new_page()
        
        # Set page-level performance optimizations
        await page.set_viewport_size({"width": 800, "height": 600})  # Smaller viewport
        
        # Block unnecessary resources to reduce CPU usage
        await page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}", lambda route: route.abort())
        # await page.route("**/*.{css}", lambda route: route.abort())  # Block CSS files - disabled due to stability issues
        
        await page.add_init_script("""
            // Disable animations and transitions
            const style = document.createElement('style');
            style.textContent = '* { animation: none !important; transition: none !important; }';
            document.head.appendChild(style);
        """)
        
        try:
            await page.goto(base_url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            logger.error(f"Failed to load main page: {e}")
            await browser.close()
            return

        # Wait for "View Details" links to load
        try:
            await page.wait_for_selector("a", timeout=30000)
        except Exception as e:
            logger.error(f"Failed to find any links on page: {e}")
            await browser.close()
            return

        # Debug: Let's see what's on the page
        logger.info("🔍 Debugging page content...")
        
        # Check for pagination info
        try:
            pagination_text = await page.text_content("body")
            if "page" in pagination_text.lower() or "results" in pagination_text.lower():
                logger.info("   📄 Found pagination/results text in page")
        except Exception as e:
            logger.warning(f"Could not check pagination text: {e}")
        
        # Check for any buttons or links that might load more content
        try:
            buttons = await page.query_selector_all("button")
            logger.info(f"   🔘 Found {len(buttons)} buttons on page")
            
            for i, button in enumerate(buttons[:5]):  # Show first 5 buttons
                try:
                    button_text = await button.text_content()
                    logger.info(f"      Button {i+1}: {button_text}")
                except Exception as e:
                    logger.debug(f"Could not get button {i+1} text: {e}")
        except Exception as e:
            logger.warning(f"Could not check buttons: {e}")
        
        # Check for any hidden elements or containers
        try:
            # Look for containers that might hold more results
            containers = await page.query_selector_all("[class*='result'], [class*='item'], [class*='list'], [class*='grid']")
            logger.info(f"   📦 Found {len(containers)} potential result containers")
            
            # Check if there are any elements with "236" or similar numbers
            elements_with_numbers = await page.query_selector_all("*")
            for elem in elements_with_numbers[:20]:  # Check first 20 elements
                try:
                    text = await elem.text_content()
                    if text and ("236" in text or "200" in text or "300" in text):
                        logger.info(f"   🔢 Found element with number: {text[:50]}...")
                except Exception as e:
                    continue
        except Exception as e:
            logger.warning(f"Could not check containers: {e}")
        
        # Try to click "Parties" button to load all results
        try:
            parties_button = await page.wait_for_selector("button:has-text('Parties')", timeout=5000)
            if parties_button:
                logger.info("   🔘 Clicking 'Parties' button to load all party results...")
                
                # Get the current URL before clicking
                current_url = page.url
                logger.info(f"   🔗 URL before click: {current_url}")
                
                # Click the button
                await parties_button.click()
                await page.wait_for_timeout(8000)  # Wait longer for all results to load
                
                # Check if URL changed
                new_url = page.url
                if new_url != current_url:
                    logger.info(f"   🔗 URL changed to: {new_url}")
                else:
                    logger.info("   🔗 URL did not change")
                
                # Check if we got more results
                initial_links = await page.eval_on_selector_all(
                    "a",
                    """elements => 
                    elements
                      .filter(el => el.textContent.includes("View Details"))
                      .map(el => el.href)
                    """
                )
                logger.info(f"   📊 After clicking 'Parties': Found {len(initial_links)} links")
                
                if len(initial_links) > 20:
                    logger.info("   ✅ Successfully loaded more results!")
                else:
                    logger.warning("   ⚠️ Still only showing 20 results, trying alternative approach...")
                    
                    # Try clicking the button again or check if URL changed
                    current_url = page.url
                    logger.info(f"   🔗 Current URL: {current_url}")
                    
                    # Try clicking the button again
                    try:
                        await parties_button.click()
                        await page.wait_for_timeout(5000)
                        
                        # Check if URL changed
                        new_url = page.url
                        if new_url != current_url:
                            logger.info(f"   🔗 URL changed to: {new_url}")
                        
                        # Check results again
                        new_links = await page.eval_on_selector_all(
                            "a",
                            """elements => 
                            elements
                              .filter(el => el.textContent.includes("View Details"))
                              .map(el => el.href)
                            """
                        )
                        logger.info(f"   📊 After second click: Found {len(new_links)} links")
                        
                        if len(new_links) > 20:
                            logger.info("   ✅ Second click worked!")
                            initial_links = new_links
                    except Exception as e:
                        logger.error(f"   ❌ Second click attempt failed: {e}")
                        
                    # Try navigating to a different URL pattern
                    try:
                        logger.info("   🔍 Trying to navigate to a different URL pattern...")
                        # Try adding parameters to the URL
                        test_url = current_url + "?limit=236&show_all=true"
                        logger.info(f"   🔗 Trying URL: {test_url}")
                        await page.goto(test_url, wait_until="domcontentloaded")
                        await page.wait_for_timeout(5000)
                        
                        test_links = await page.eval_on_selector_all(
                            "a",
                            """elements => 
                            elements
                              .filter(el => el.textContent.includes("View Details"))
                              .map(el => el.href)
                            """
                        )
                        logger.info(f"   📊 Test URL results: Found {len(test_links)} links")
                        
                        if len(test_links) > 20:
                            logger.info("   ✅ Test URL worked!")
                            initial_links = test_links
                        else:
                            # Go back to original URL
                            await page.goto(current_url, wait_until="domcontentloaded")
                    except Exception as e:
                        logger.error(f"   ❌ Test URL attempt failed: {e}")
        except Exception as e:
            logger.warning(f"   ⚠️ 'Parties' button not found, proceeding with current results: {e}")

        # Extract all URLs with "View Details" text
        try:
            detail_links = await page.eval_on_selector_all(
                "a",
                """elements => 
                elements
                  .filter(el => el.textContent.includes("View Details"))
                  .map(el => el.href)
                """
            )
        except Exception as e:
            logger.error(f"Failed to extract detail links: {e}")
            await browser.close()
            return

        # Check if there are more pages to load
        previous_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 100  # Much more scroll attempts to capture all links
        
        while scroll_attempts < max_scroll_attempts:
            try:
                # Scroll to bottom to load more content
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(3000)  # Wait longer for content to load
                
                # Get updated links
                new_links = await page.eval_on_selector_all(
                    "a",
                    """elements => 
                    elements
                      .filter(el => el.textContent.includes("View Details"))
                      .map(el => el.href)
                    """
                )
                
                logger.info(f"Found {len(new_links)} links after scroll {scroll_attempts + 1}")
                
                if len(new_links) <= previous_count:
                    scroll_attempts += 1
                    if scroll_attempts >= 3:  # Try 3 more times after no new links
                        break
                else:
                    scroll_attempts = 0  # Reset counter if we found new links
                    
                detail_links = new_links
                previous_count = len(new_links)
            except Exception as e:
                logger.warning(f"Error during scroll attempt {scroll_attempts + 1}: {e}")
                scroll_attempts += 1
                if scroll_attempts >= 5:  # Stop after 5 scroll errors
                    break

        logger.info(f"Found {len(detail_links)} links.")

        # Print all links to screen
        for i, link in enumerate(detail_links, 1):
            logger.info(f"{i}. {link}")

        # Store results for file output
        results = []
        failed_parties = []  # Track parties that failed for retry

        # Process URLs in parallel batches with multiple passes
        batch_size = 25  # Process 25 pages at a time (reduced for lower CPU usage)
        max_passes = 3  # Maximum number of retry passes
        
        logger.info(f"\n🚀 Processing {len(detail_links)} pages in parallel batches of {batch_size}...")
        
        # First pass - process all parties
        current_links = detail_links.copy()
        
        for pass_num in range(1, max_passes + 1):
            if not current_links:
                logger.info(f"✅ No more parties to process in pass {pass_num}")
                break
                
            logger.info(f"\n🔄 PASS {pass_num}/{max_passes} - Processing {len(current_links)} parties...")
            
            # Process current batch of links
            for i in range(0, len(current_links), batch_size):
                batch = current_links[i:i + batch_size]
                logger.info(f"\n📦 Processing batch {i//batch_size + 1}/{(len(current_links) + batch_size - 1)//batch_size}")
                
                # Process batch in parallel with better error handling
                try:
                    batch_results = await asyncio.gather(*[process_single_page(url, browser, pass_num) for url in batch], return_exceptions=True)
                    
                    # Handle exceptions from gather
                    for j, result in enumerate(batch_results):
                        if isinstance(result, Exception):
                            party_name = extract_party_name_from_url(batch[j])
                            logger.error(f"   ❌ {party_name}: Exception in batch processing - {result}")
                            batch_results[j] = {
                                "party": party_name,
                                "balance": f"Batch Error: {str(result)}",
                                "url": batch[j]
                            }
                    
                    # Add successful results to final results
                    for result in batch_results:
                        if isinstance(result, dict):
                            results.append(result)
                            # If this party failed, add to retry list for next pass
                            if result.get('balance') == 'Not found' or 'Error:' in str(result.get('balance', '')):
                                failed_parties.append(result['url'])
                    
                    # Add a small delay between batches to reduce CPU load
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    # Add error entries for this batch
                    for url in batch:
                        party_name = extract_party_name_from_url(url)
                        results.append({
                            "party": party_name,
                            "balance": f"Batch Error: {str(e)}",
                            "url": url
                        })
                        failed_parties.append(url)
            
            # Update current_links for next pass (only failed parties)
            current_links = failed_parties.copy()
            failed_parties = []  # Reset for next pass
            
            if current_links:
                logger.info(f"🔄 Pass {pass_num} complete. {len(current_links)} parties failed, retrying in pass {pass_num + 1}...")
                # Add longer delay between passes
                await asyncio.sleep(5)
            else:
                logger.info(f"✅ Pass {pass_num} complete. All parties processed successfully!")

        # Write results to file
        logger.info(f"\n💾 Writing results to codascan_balances.txt...")
        try:
            with open("codascan_balances.txt", "w") as f:
                f.write("Party Name\tParty ID\tBalance\tURL\n")
                for result in results:
                    # Extract partyid from URL
                    partyid = extract_party_id_from_url(result['url'])
                    f.write(f"{result['party']}\t{partyid}\t{result['balance']}\t{result['url']}\n")
            
            logger.info(f"✅ Results saved to codascan_balances.txt")
        except Exception as e:
            logger.error(f"Failed to write results file: {e}")
        
        # Write error summary
        error_count = sum(1 for r in results if 'Error:' in str(r.get('balance', '')))
        not_found_count = sum(1 for r in results if r.get('balance') == 'Not found')
        success_count = len(results) - error_count - not_found_count
        
        logger.info(f"📊 Processed {len(results)} parties")
        logger.info(f"✅ Successful: {success_count}")
        logger.info(f"❌ Errors: {error_count}")
        logger.info(f"🔍 Not found: {not_found_count}")

        await browser.close()

async def process_single_page(url, browser, pass_num=1):
    """Process a single page and extract balance with retry logic"""
    # Extract party name from URL
    party_name = extract_party_name_from_url(url)
    logger.info(f"   🔍 Processing: {party_name}")
    
    # Progressive wait times based on pass number
    if pass_num == 1:
        wait_times = [15000, 25000, 35000]  # Standard wait times
        max_retries = 3
    elif pass_num == 2:
        wait_times = [25000, 35000, 45000]  # Longer wait times for retry
        max_retries = 3
    else:  # pass_num == 3
        wait_times = [35000, 45000, 60000]  # Even longer wait times for final attempt
        max_retries = 3
    
    for attempt in range(max_retries):
        detail_page = await browser.new_page()
        
        # Apply performance optimizations to detail pages
        await detail_page.set_viewport_size({"width": 800, "height": 600})
        await detail_page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}", lambda route: route.abort())
        # await detail_page.route("**/*.{css}", lambda route: route.abort())  # Disabled due to stability issues
        
        current_wait_time = wait_times[min(attempt, len(wait_times) - 1)]
        
        try:
            # Set longer timeout for network issues
            await detail_page.goto(url, wait_until="domcontentloaded", timeout=45000)
            
            # Wait for dynamic content to load with progressive timing
            logger.info(f"   ⏱️ Pass {pass_num}, Attempt {attempt + 1}/{max_retries} - Waiting {current_wait_time/1000}s for content...")
            await detail_page.wait_for_timeout(current_wait_time)
            
            # Try to wait for specific elements that might contain balance
            try:
                await detail_page.wait_for_selector("text=Balance", timeout=10000)
            except Exception as e:
                try:
                    await detail_page.wait_for_selector("[class*='balance']", timeout=5000)
                except Exception as e:
                    try:
                        await detail_page.wait_for_selector("[class*='amount']", timeout=5000)
                    except Exception as e:
                        # If we can't find balance elements, try a longer wait on retry
                        if attempt < max_retries - 1:
                            logger.info(f"   🔍 No balance elements found, will retry with longer wait...")
                        pass
            
            # Additional debugging for bitsafe minter
            if "bitsafe" in party_name.lower() or "minter" in party_name.lower():
                logger.info(f"   🔍 Debug - Checking page for {party_name}...")
                
                # Try to find any elements with numbers
                try:
                    number_elements = await detail_page.query_selector_all("*")
                    for elem in number_elements[:50]:  # Check first 50 elements
                        try:
                            text = await elem.text_content()
                            if text and re.search(r'[0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+', text):
                                logger.info(f"   🔢 Found number element: {text[:100]}...")
                        except Exception as e:
                            continue
                except Exception as e:
                    pass
                
                # Try to wait for any dynamic content
                try:
                    await detail_page.wait_for_timeout(5000)  # Wait a bit more
                    # Try clicking any buttons that might load balance
                    buttons = await detail_page.query_selector_all("button")
                    for button in buttons[:5]:
                        try:
                            button_text = await button.text_content()
                            if "load" in button_text.lower() or "refresh" in button_text.lower():
                                logger.info(f"   🔘 Clicking button: {button_text}")
                                await button.click()
                                await detail_page.wait_for_timeout(3000)
                        except Exception as e:
                            continue
                except Exception as e:
                    pass
            
            # Get the page content after waiting
            content = await detail_page.content()
            text_content = await detail_page.text_content("body")
            
            # Check if we got meaningful content
            if not text_content or len(text_content.strip()) < 100:
                if attempt < max_retries - 1:
                    logger.warning(f"   ⚠️ {party_name}: Page content too short ({len(text_content)} chars), retrying...")
                    continue
                else:
                    logger.error(f"   ❌ {party_name}: Page content too short after all retries")
                    return {
                        "party": party_name,
                        "balance": "Not found",
                        "url": url
                    }
            
            # Debug: Log what we found for problematic parties
            if party_name in ["flowdesk", "gemini", "hashnote", "noders", "redstone"]:
                logger.info(f"   🔍 Debug - {party_name} text content (first 200 chars): {text_content[:200]}")
                import re
                decimal_matches = re.findall(r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)', text_content)
                logger.info(f"   🔢 Debug - {party_name} decimal numbers found: {decimal_matches[:5]}")
            
            # Extract balance using multiple methods
            balance = extract_balance_from_html(content, text_content)
            if balance:
                logger.info(f"   ✅ {party_name}: {balance}")
                return {
                    "party": party_name,
                    "balance": balance,
                    "url": url
                }
            else:
                logger.warning(f"   ❌ {party_name}: No balance found")
                return {
                    "party": party_name,
                    "balance": "Not found",
                    "url": url
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"   ⚠️ {party_name}: Pass {pass_num}, Attempt {attempt + 1}/{max_retries} failed - {error_msg}")
            
            # Check if it's a network error that might be retryable
            if any(network_error in error_msg.lower() for network_error in ['timeout', 'network', 'connection', 'socket']):
                if attempt < max_retries - 1:
                    next_wait_time = wait_times[min(attempt + 1, len(wait_times) - 1)] / 1000
                    logger.info(f"   🔄 Retrying {party_name} in 2 seconds with longer wait time ({next_wait_time}s)...")
                    await asyncio.sleep(2)
                    continue
            else:
                # Non-network error, don't retry
                break
                
        finally:
            await detail_page.close()
    
    # All retries failed
    logger.error(f"   ❌ {party_name}: All {max_retries} attempts failed in pass {pass_num}")
    return {
        "party": party_name,
        "balance": f"Error: {error_msg}",
        "url": url
    }

def extract_balance_from_html(html_content, text_content):
    """Extract wallet balance from HTML content using various patterns"""
    
    # Debug: Let's see what's actually in the text content for debugging
    if "bitsafe" in text_content.lower() or "minter" in text_content.lower():
        logger.debug(f"   🔍 Debug - Text content for bitsafe/minter: {text_content[:500]}...")
    
    # Pattern 1: Look for balance in text content with more specific patterns
    # All patterns now require decimal places since wallet balances always have .00 format
    balance_patterns = [
        # Most specific patterns for wallet balances (always have decimals)
        r'Wallet Balance[:\s]*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',
        r'wallet balance[:\s]*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',
        r'Wallet Balance([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',  # No colon/space after "Wallet Balance"
        r'wallet balance([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',  # No colon/space after "wallet balance"
        r'Balance[:\s]*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',
        r'balance[:\s]*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',
        r'Balance([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',  # No colon/space after "Balance"
        r'balance([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',  # No colon/space after "balance"
        # Look for numbers with currency symbols or units (must have decimals)
        r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)\s*CANTON',
        r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)\s*USD',
        r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)\s*ETH',
        r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)\s*coins?',
        r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)\s*tokens?',
        # Look for balance in specific contexts (must have decimals)
        r'Total[:\s]*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',
        r'Amount[:\s]*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',
        r'Holdings[:\s]*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',
        r'Assets[:\s]*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',
        # Look for numbers that are clearly balances (with decimal places)
        r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)\s*@',  # Matches numbers followed by @ symbol
        r'@\s*([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',  # Matches @ symbol followed by numbers
    ]
    
    # Search in both HTML and text content
    for pattern in balance_patterns:
        # Search in HTML content
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            balance = match.group(1)
            # Validate that this looks like a reasonable balance
            try:
                balance_float = float(balance.replace(',', ''))
                if balance_float >= 0 and balance_float < 10000000:  # Allow 0.00
                    return balance
                    
            except ValueError:
                continue
        
        # Search in text content
        if text_content:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                balance = match.group(1)
                # Validate that this looks like a reasonable balance
                try:
                    balance_float = float(balance.replace(',', ''))
                    if balance_float >= 0 and balance_float < 10000000:  # Allow 0.00
                        return balance
                except ValueError:
                    continue
    
    # Pattern 2: Look for any number with decimal places that could be a balance
    # This is more conservative but catches balances like 0.00, 199,569.2721
    decimal_number_patterns = [
        r'([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+)',  # Matches 116,825.8045 format
        r'([0-9]+\.[0-9]+)',  # Matches simple decimals like 0.00, 199.50
    ]
    
    for pattern in decimal_number_patterns:
        if text_content:
            matches = re.findall(pattern, text_content)
            if matches:
                # Return the first substantial number found that's not a year
                for match in matches:
                    try:
                        balance_float = float(match.replace(',', ''))
                        # Allow 0.00 and reasonable balance ranges, exclude years
                        if (balance_float >= 0 and balance_float < 10000000 and 
                            not (balance_float >= 1900 and balance_float <= 2030)):  # Exclude years
                            return match
                    except ValueError:
                        continue
    
    return None

def extract_party_name_from_url(url):
    """Extract party name from URL (part before ::)"""
    try:
        # Extract the party ID part from the URL
        # URL format: https://www.cantonscan.com/party/sendit%3A%3A1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
        party_part = url.split('/party/')[-1]
        # Decode URL encoding (%3A becomes :)
        decoded_part = urllib.parse.unquote(party_part)
        # Extract part before ::
        party_name = decoded_part.split('::')[0]
        return party_name
    except:
        return "Unknown"

def extract_party_id_from_url(url):
    """Extract full party ID (name::hash) from URL"""
    try:
        # Extract the party ID part from the URL
        # URL format: https://www.cantonscan.com/party/sendit%3A%3A1220409a9fcc5ff6422e29ab978c22c004dde33202546b4bcbde24b25b85353366c2
        party_part = url.split('/party/')[-1]
        # Decode URL encoding (%3A becomes :)
        decoded_part = urllib.parse.unquote(party_part)
        # Return the full party ID (name::hash)
        return decoded_part
    except:
        return "Unknown"

if __name__ == "__main__":
    asyncio.run(run())
