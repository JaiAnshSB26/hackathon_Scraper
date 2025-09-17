import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def _make_headless_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
    # Prevent opening new windows in front of the user
    opts.add_argument('--disable-infobars')
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    return driver


def _scroll_devpost_for_more_content(driver):
    """Improved scrolling for Devpost's infinite scroll with proper position tracking"""
    print("Starting Devpost scrolling...")
    
    # Wait for initial content to load
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "hackathon-tile"))
        )
        # Additional wait for any initial lazy loading
        time.sleep(3)
    except:
        print("No initial hackathon tiles found")
        return
    
    # Get initial count and scroll position
    initial_tiles = len(driver.find_elements(By.CLASS_NAME, "hackathon-tile"))
    print(f"Initial tiles found: {initial_tiles}")
    
    last_count = initial_tiles
    no_new_content_count = 0
    max_attempts_without_new_content = 5
    max_total_scrolls = 50
    
    # Track our scroll progress to avoid resetting position
    last_successful_scroll_position = 0
    
    for scroll_attempt in range(max_total_scrolls):
        print(f"\n--- Scroll attempt {scroll_attempt + 1} ---")
        
        # Safety check - make sure we're still on the hackathons page
        current_url = driver.current_url
        if '/hackathons' not in current_url:
            print(f"ERROR: Not on hackathons page anymore! Current URL: {current_url}")
            print("Attempting to return to hackathons page...")
            driver.get('https://devpost.com/hackathons')
            time.sleep(5)
            # Re-check tile count after returning
            current_tiles = len(driver.find_elements(By.CLASS_NAME, "hackathon-tile"))
            print(f"After returning to hackathons page, found {current_tiles} tiles")
            if current_tiles < last_count:
                print(f"WARNING: Tile count decreased from {last_count} to {current_tiles}")
                # Continue with current count
                last_count = current_tiles
        
        # Store current state before scrolling
        current_tiles = len(driver.find_elements(By.CLASS_NAME, "hackathon-tile"))
        current_height = driver.execute_script("return document.body.scrollHeight")
        current_scroll_pos = driver.execute_script("return window.pageYOffset")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        print(f"Current position: {current_scroll_pos}, Page height: {current_height}")
        print(f"Current tiles: {current_tiles}")
        
        # Calculate how much to scroll - continue from where we left off
        # If we're not near the bottom, scroll down by viewport height
        if current_scroll_pos + viewport_height < current_height - 200:
            # Scroll by viewport height to continue from current position
            new_scroll_position = current_scroll_pos + viewport_height
            driver.execute_script(f"window.scrollTo(0, {new_scroll_position});")
            print(f"Scrolled to position: {new_scroll_position}")
        else:
            # We're near the bottom, scroll to the absolute bottom to trigger loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            new_scroll_position = driver.execute_script("return window.pageYOffset")
            print(f"Scrolled to bottom: {new_scroll_position}")
        
        # Wait for content to load
        time.sleep(3)
        
        # Check what happened after scrolling
        after_scroll_tiles = len(driver.find_elements(By.CLASS_NAME, "hackathon-tile"))
        after_scroll_height = driver.execute_script("return document.body.scrollHeight")
        after_scroll_pos = driver.execute_script("return window.pageYOffset")
        
        print(f"After scroll - Tiles: {current_tiles} -> {after_scroll_tiles}")
        print(f"After scroll - Height: {current_height} -> {after_scroll_height}")
        print(f"After scroll - Position: {current_scroll_pos} -> {after_scroll_pos}")
        
        # Check if we got new tiles
        if after_scroll_tiles > current_tiles:
            gained = after_scroll_tiles - current_tiles
            print(f"✓ Loaded {gained} new hackathons")
            last_count = after_scroll_tiles
            no_new_content_count = 0
            last_successful_scroll_position = after_scroll_pos
            
            # Give extra time for newly loaded content to settle and for potential additional loading
            time.sleep(4)
            
        # Check if page height increased (indicating new content being loaded)
        elif after_scroll_height > current_height:
            print("✓ Page height increased, waiting for tiles to appear...")
            time.sleep(5)  # Give more time for content to render
            
            # Check again for new tiles
            final_tiles = len(driver.find_elements(By.CLASS_NAME, "hackathon-tile"))
            if final_tiles > current_tiles:
                gained = final_tiles - current_tiles
                print(f"✓ Loaded {gained} new hackathons after height change")
                last_count = final_tiles
                no_new_content_count = 0
                last_successful_scroll_position = after_scroll_pos
            else:
                no_new_content_count += 1
                print(f"✗ Height increased but no new tiles ({no_new_content_count}/{max_attempts_without_new_content})")
        else:
            no_new_content_count += 1
            print(f"✗ No new content detected ({no_new_content_count}/{max_attempts_without_new_content})")
        
        # Try to find and click load more buttons (but be very specific to avoid clicking hackathon links)
        load_more_clicked = False
        try:
            # Very specific selectors for actual load more buttons, avoiding hackathon content
            load_more_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]", 
                "//a[@class and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
                "//a[@class and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]",
                "//*[@role='button' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
                "//*[@role='button' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]"
            ]
            
            for selector in load_more_selectors:
                try:
                    buttons = driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip()
                            # Very strict validation - must be exactly a load more type button
                            text_lower = button_text.lower()
                            
                            # Exclude anything that looks like hackathon content
                            exclude_patterns = [
                                'hackathon', 'competition', 'challenge', 'cyber', 'tech', 'ai', 
                                'machine learning', 'blockchain', 'app', 'web', 'mobile', 'game',
                                'innovation', 'startup', 'coding', 'programming', 'development'
                            ]
                            
                            # Skip if it contains hackathon-like terms
                            if any(pattern in text_lower for pattern in exclude_patterns):
                                print(f"Skipping potential hackathon link: '{button_text}'")
                                continue
                            
                            # Only click if it's clearly a load more button
                            valid_patterns = [
                                'load more', 'show more', 'view more', 'see more',
                                'load all', 'show all', 'view all'
                            ]
                            
                            if any(pattern in text_lower for pattern in valid_patterns):
                                print(f"Found valid load more button: '{button_text}'")
                                
                                # Double-check we're still on the hackathons page
                                current_url = driver.current_url
                                if '/hackathons' not in current_url:
                                    print(f"Not on hackathons page anymore: {current_url}")
                                    break
                                
                                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", button)
                                time.sleep(5)  # Wait for content to load
                                
                                # Verify we're still on the right page after clicking
                                new_url = driver.current_url
                                if '/hackathons' not in new_url:
                                    print(f"Button click navigated away from hackathons page to: {new_url}")
                                    # Try to go back
                                    driver.get('https://devpost.com/hackathons')
                                    time.sleep(5)
                                    break
                                
                                load_more_clicked = True
                                no_new_content_count = 0
                                break
                            else:
                                print(f"Button text doesn't match load more patterns: '{button_text}'")
                                
                    if load_more_clicked:
                        break
                        
                except Exception as e:
                    print(f"Error checking selector {selector}: {e}")
                    continue
                    
            if load_more_clicked:
                # After clicking load more, check for new content
                new_tile_count = len(driver.find_elements(By.CLASS_NAME, "hackathon-tile"))
                if new_tile_count > after_scroll_tiles:
                    print(f"✓ Load more button added {new_tile_count - after_scroll_tiles} tiles")
                    last_count = new_tile_count
                else:
                    print(f"Load more button didn't add tiles (still {new_tile_count})")
                
        except Exception as e:
            print(f"Error with load more buttons: {e}")
        
        # Enhanced stopping conditions
        current_final_scroll = driver.execute_script("return window.pageYOffset")
        current_final_height = driver.execute_script("return document.body.scrollHeight")
        
        # Stop if no new content AND we're at the bottom AND no buttons clicked
        at_bottom = current_final_scroll + viewport_height >= current_final_height - 100
        
        if no_new_content_count >= max_attempts_without_new_content and at_bottom and not load_more_clicked:
            print(f"\nStopping: No new content for {no_new_content_count} attempts and reached bottom")
            break
            
        # Also stop if we've been at the same scroll position for too long
        if (not load_more_clicked and 
            abs(current_final_scroll - last_successful_scroll_position) < 100 and 
            no_new_content_count >= 3):
            print(f"\nStopping: Stuck at same scroll position")
            break
    
    final_count = len(driver.find_elements(By.CLASS_NAME, "hackathon-tile"))
    print(f"\nScrolling complete!")
    print(f"Initial: {initial_tiles} -> Final: {final_count}")
    print(f"Total gained: {final_count - initial_tiles}")
    
    return final_count


def _parse_devpost(soup):
    hackathons = []
    hackathon_tiles = soup.find_all('div', class_='hackathon-tile')
    
    if not hackathon_tiles:
        print("No hackathon tiles found")
        return hackathons
    
    print(f"Parsing {len(hackathon_tiles)} hackathon tiles...")
    
    for i, hackathon in enumerate(hackathon_tiles):
        try:
            title_tag = hackathon.find('h3', class_='mb-4')
            date_tag = hackathon.find('div', class_='submission-period')
            link_tag = hackathon.find('a', class_='flex-row')
            
            if title_tag and date_tag and link_tag:
                title = title_tag.text.strip()
                date = date_tag.text.strip()
                link = link_tag['href']
                
                if link.startswith('/'):
                    link = f"https://devpost.com{link}"
                
                hackathons.append({'title': title, 'date': date, 'link': link})
            else:
                print(f"Skipping hackathon {i+1}: missing required data")
                # Debug what's missing
                if not title_tag:
                    print("  - Missing title")
                if not date_tag:
                    print("  - Missing date")  
                if not link_tag:
                    print("  - Missing link")
        except Exception as e:
            print(f"Error parsing hackathon {i+1}: {e}")
    
    print(f"Successfully parsed {len(hackathons)} hackathons")
    return hackathons


def scrape_devpost():
    """Scrape devpost.com/hackathons and return a list of hackathon dicts.

    This function runs Chrome headless and scrolls to load more results.
    """
    print("Starting Devpost scraping...")
    driver = _make_headless_driver()
    try:
        print("Navigating to Devpost...")
        driver.get('https://devpost.com/hackathons')
        print("Page loaded, waiting for initial content...")
        time.sleep(5)  # Give initial content time to load
        
        # Use the improved scrolling mechanism
        final_count = _scroll_devpost_for_more_content(driver)
        
        print("Getting page source for parsing...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
    finally:
        driver.quit()
    
    return _parse_devpost(soup)


def scrape_devfolio():
    hackathons = []
    driver = _make_headless_driver()
    try:
        driver.get('https://devfolio.co/hackathons')
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    hackathon_group = soup.find_all('div', class_='sc-fmGnzW')
    for hackathon in hackathon_group:
        link_tag = hackathon.find('a', class_='lkflLS')  # text confusing, try 1 instead of l in case of error
        date_tag = hackathon.find('p', class_='cqgLqk')
        title_tag = hackathon.find('h3', class_='sc-dkzDqf')
        if title_tag and date_tag and link_tag:
            title = title_tag.text.strip()
            date = date_tag.text.strip()
            link = link_tag['href']
            if link.startswith('/'):
                link = f"https://devfolio.com{link}"
            hackathons.append({'title': title, 'date': date, 'link': link})
        else:
            print("Skipping a hackathon due to missing data:", hackathon)
    return hackathons


def scrape_mlh():
    hackathons = []
    driver = _make_headless_driver()
    try:
        driver.get('https://mlh.io/seasons/2025/events')
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    hackathon_container = soup.find_all('div', class_='event')
    for hackathon in hackathon_container:
        title_tag = hackathon.find('h3', class_='event-name')
        link_tag = hackathon.find('a', class_='event-link')
        date_tag = hackathon.find('p', class_='event-date')
        if title_tag and date_tag and link_tag:
            title = title_tag.text.strip()
            date = date_tag.text.strip()
            link = link_tag['href']
            if link.startswith('/'):
                link = f"https://mlh.io/seasons/2025/events{link}"
            hackathons.append({'title': title, 'date': date, 'link': link})
        else:
            print("Skipping a hackathon due to missing data:", hackathon)
    return hackathons


def scrape_hackathon_com():
    hackathons = []
    driver = _make_headless_driver()
    try:
        driver.get('https://www.hackathon.com/online')
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    all_hackathons = soup.find_all('div', class_='ht-eb-card')
    for hackathon in all_hackathons:
        title_tag = hackathon.find('a', class_='ht-eb-card__title')
        link_tag = hackathon.find('a', class_='ht-eb-card__title')
        date = ''
        start_date = hackathon.find('div', class_='date--start')
        if start_date:
            date += start_date.find('div', class_='date__title').text.strip()
            date += ' '
            date += start_date.find('div', class_='date__day').text.strip()
            date += ' '
            date += start_date.find('div', class_='date__month').text.strip()
        date += ' '
        end_date = hackathon.find('div', class_='date--end')
        if end_date:
            date += end_date.find('div', class_='date__title').text.strip()
            date += ' '
            date += end_date.find('div', class_='date__day').text.strip()
            date += ' '
            date += end_date.find('div', class_='date__month').text.strip()
        if title_tag and link_tag:
            title = title_tag.text.strip()
            link = link_tag['href']
            if link.startswith('/'):
                link = f"https://www.hackathon.com/online{link}"
            hackathons.append({'title': title, 'date': date, 'link': link})
        else:
            print("Skipping a hackathon due to missing data:", hackathon)
    return hackathons


def fetch_all_hackathons():
    """Run all scrapers and return a combined list.

    Order: Devpost (scrolling), Devfolio, MLH, Hackathon.com
    """
    results = []
    print("=== Starting comprehensive hackathon scraping ===")
    
    print("\n1. Scraping Devpost...")
    try:
        devpost_results = scrape_devpost()
        results.extend(devpost_results)
        print(f"Devpost: {len(devpost_results)} hackathons")
    except Exception as e:
        print(f"Devpost failed: {e}")
        
    print("\n2. Scraping Devfolio...")
    try:
        devfolio_results = scrape_devfolio()
        results.extend(devfolio_results)
        print(f"Devfolio: {len(devfolio_results)} hackathons")
    except Exception as e:
        print(f"Devfolio failed: {e}")
        
    print("\n3. Scraping MLH...")
    try:
        mlh_results = scrape_mlh()
        results.extend(mlh_results)
        print(f"MLH: {len(mlh_results)} hackathons")
    except Exception as e:
        print(f"MLH failed: {e}")
        
    print("\n4. Scraping Hackathon.com...")
    try:
        hackathon_com_results = scrape_hackathon_com()
        results.extend(hackathon_com_results)
        print(f"Hackathon.com: {len(hackathon_com_results)} hackathons")
    except Exception as e:
        print(f"Hackathon.com failed: {e}")

    print(f"\nTotal before deduplication: {len(results)}")
    
    # Deduplicate by title+link
    seen = set()
    unique = []
    for h in results:
        key = (h.get('title'), h.get('link'))
        if key in seen:
            continue
        seen.add(key)
        unique.append(h)
    
    print(f"Total after deduplication: {len(unique)}")
    print("=== Scraping complete ===")
    return unique