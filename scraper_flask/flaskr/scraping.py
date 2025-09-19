import time
import threading
import concurrent.futures
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
    
    # Enhanced performance optimizations
    opts.add_argument('--disable-infobars')
    opts.add_argument('--disable-extensions')
    opts.add_argument('--disable-plugins')
    opts.add_argument('--disable-images')  # Don't load images for faster loading
    opts.add_argument('--disable-background-timer-throttling')
    opts.add_argument('--disable-renderer-backgrounding')
    opts.add_argument('--disable-backgrounding-occluded-windows')
    opts.add_argument('--disable-features=TranslateUI')
    opts.add_argument('--disable-ipc-flooding-protection')
    opts.add_argument('--disable-web-security')  # Faster loading
    opts.add_argument('--disable-features=VizDisplayCompositor')
    opts.add_argument('--memory-pressure-off')
    opts.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    opts.add_experimental_option('useAutomationExtension', False)
    
    # Aggressive performance settings
    opts.add_experimental_option('prefs', {
        'profile.default_content_setting_values.notifications': 2,
        'profile.default_content_settings.popups': 0,
        'profile.managed_default_content_settings.images': 2,
        'profile.default_content_setting_values.media_stream': 2,
        'profile.default_content_settings.geolocation': 2,
        'profile.default_content_settings.microphone': 2,
        'profile.default_content_settings.camera': 2,
    })
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    # Faster timeouts
    driver.set_page_load_timeout(15)  # Reduced from 30
    driver.implicitly_wait(2)  # Reduced from 5
    return driver


def _fast_scroll_devpost(driver):
    """Optimized scrolling for Devpost with faster timing and smarter detection"""
    print("Starting optimized Devpost scrolling...")
    
    # Wait for initial content with shorter timeout
    try:
        WebDriverWait(driver, 6).until(  # Reduced from 10
            EC.presence_of_element_located((By.CLASS_NAME, "hackathon-tile"))
        )
        time.sleep(1)  # Reduced from 2
    except:
        print("No initial hackathon tiles found")
        return 0
    
    initial_tiles = len(driver.find_elements(By.CLASS_NAME, "hackathon-tile"))
    print(f"Initial tiles: {initial_tiles}")
    
    last_count = initial_tiles
    stagnant_attempts = 0
    max_stagnant = 5  # Reduced patience for speed
    max_scrolls = 100
    
    # Pre-calculate scroll positions for speed
    viewport_height = driver.execute_script("return window.innerHeight")
    scroll_increment = viewport_height * 0.8  # Larger, smarter increments
    
    for attempt in range(max_scrolls):
        # Get current state in one script execution (faster)
        scroll_data = driver.execute_script("""
            return {
                tiles: document.querySelectorAll('.hackathon-tile').length,
                height: document.body.scrollHeight,
                scroll: window.pageYOffset,
                viewport: window.innerHeight
            };
        """)
        
        current_tiles = scroll_data['tiles']
        current_height = scroll_data['height']
        current_scroll = scroll_data['scroll']
        viewport_height = scroll_data['viewport']
        
        # Smart scrolling strategy - larger jumps
        if current_scroll + viewport_height >= current_height - 500:
            # Near bottom - jump to absolute bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            # Large progressive jumps
            new_pos = current_scroll + scroll_increment
            driver.execute_script(f"window.scrollTo(0, {new_pos});")
        
        # Shorter wait with early detection
        time.sleep(0.8)  # Reduced from 1.5
        
        # Quick batch check for changes
        quick_check = driver.execute_script("""
            return {
                tiles: document.querySelectorAll('.hackathon-tile').length,
                height: document.body.scrollHeight
            };
        """)
        
        new_tiles = quick_check['tiles']
        new_height = quick_check['height']
        
        if new_tiles > current_tiles or new_height > current_height:
            gained = new_tiles - current_tiles
            last_count = new_tiles
            stagnant_attempts = 0
            if gained > 0:
                print(f"  Scroll {attempt + 1}: +{gained} tiles (total: {new_tiles})")
            
            # Very short wait after finding content
            time.sleep(0.5)  # Reduced from 1
        else:
            stagnant_attempts += 1
            print(f"  Scroll {attempt + 1}: No new content ({stagnant_attempts}/{max_stagnant})")
        
        # Quick button check only when needed
        if stagnant_attempts == 2 and attempt < max_scrolls - 10:  # Skip near end
            try:
                # Single XPath for all button types
                button = driver.find_element(By.XPATH, 
                    "//button[contains(translate(text(), 'ML', 'ml'), 'more')] | " +
                    "//a[contains(translate(text(), 'ML', 'ml'), 'more')]"
                )
                
                if button.is_displayed() and button.is_enabled():
                    print(f"  → Clicking: {button.text[:20]}")
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(1.5)  # Reduced from 3
                    stagnant_attempts = 0
            except:
                pass
        
        # Early termination with progress logging
        if stagnant_attempts >= max_stagnant:
            print(f"  → Stopping after {attempt+1} scrolls: {stagnant_attempts} stagnant attempts")
            break
        
        # Progress update every 15 scrolls instead of 10
        if attempt % 15 == 0 and attempt > 0:
            print(f"  → Scroll checkpoint {attempt}: {current_tiles} tiles")
    
    final_count = len(driver.find_elements(By.CLASS_NAME, "hackathon-tile"))
    print(f"Devpost scrolling complete: {initial_tiles} → {final_count} (+{final_count - initial_tiles})")
    return final_count


def _parse_devpost(soup):
    """Optimized parsing with batch processing"""
    hackathons = []
    tiles = soup.find_all('div', class_='hackathon-tile')
    
    if not tiles:
        return hackathons
    
    print(f"Parsing {len(tiles)} tiles...")
    parsed_count = 0
    
    for tile in tiles:
        try:
            title_tag = tile.find('h3', class_='mb-4')
            date_tag = tile.find('div', class_='submission-period')
            link_tag = tile.find('a', class_='flex-row')
            
            if all([title_tag, date_tag, link_tag]):
                title = title_tag.get_text(strip=True)
                date = date_tag.get_text(strip=True)
                link = link_tag.get('href')
                
                if link and link.startswith('/'):
                    link = f"https://devpost.com{link}"
                
                hackathons.append({'title': title, 'date': date, 'link': link})
                parsed_count += 1
        except:
            continue
    
    print(f"Successfully parsed: {parsed_count}/{len(tiles)}")
    return hackathons


def scrape_devpost():
    """Optimized Devpost scraping"""
    print("Starting optimized Devpost scraping...")
    driver = _make_headless_driver()
    try:
        driver.get('https://devpost.com/hackathons')
        time.sleep(1.5)  # Reduced from 3
        
        final_count = _fast_scroll_devpost(driver)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
    finally:
        driver.quit()
    
    return _parse_devpost(soup)


def scrape_devfolio():
    """Optimized Devfolio scraping"""
    driver = _make_headless_driver()
    try:
        driver.get('https://devfolio.co/hackathons')
        time.sleep(1.5)  # Reduced from 3
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    hackathons = []
    for hackathon in soup.find_all('div', class_='sc-bczRLJ'):
        try:
            title = hackathon.find('h3', class_='sc-hKMtZM').get_text(strip=True)
            date = hackathon.find('p', class_='sc-hKMtZM').get_text(strip=True)
            link = hackathon.find('a', class_='bnxtME').get('href')
            
            if link.startswith('/'):
                link = f"https://devfolio.com{link}"
            
            hackathons.append({'title': title, 'date': date, 'link': link})
        except:
            continue
    
    print(f"Devfolio: Found {len(hackathons)} hackathons")
    return hackathons


def scrape_mlh():
    """Optimized MLH scraping"""
    driver = _make_headless_driver()
    try:
        driver.get('https://mlh.io/seasons/2025/events')
        time.sleep(1.5)  # Reduced from 3
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    hackathons = []
    for event in soup.find_all('div', class_='event'):
        try:
            title = event.find('h3', class_='event-name').get_text(strip=True)
            date = event.find('p', class_='event-date').get_text(strip=True)
            link = event.find('a', class_='event-link').get('href')
            
            if link.startswith('/'):
                link = f"https://mlh.io{link}"
            
            hackathons.append({'title': title, 'date': date, 'link': link})
        except:
            continue
    
    print(f"MLH: Found {len(hackathons)} hackathons")
    return hackathons


def scrape_hackathon_com():
    """Optimized Hackathon.com scraping"""
    driver = _make_headless_driver()
    try:
        driver.get('https://www.hackathon.com/online')
        time.sleep(1.5)  # Reduced from 3
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    hackathons = []
    for card in soup.find_all('div', class_='ht-eb-card'):
        try:
            title_tag = card.find('a', class_='ht-eb-card__title')
            if not title_tag:
                continue
                
            title = title_tag.get_text(strip=True)
            link = title_tag.get('href')
            
            # Build date string
            date_parts = []
            for date_div in card.find_all('div', class_=['date--start', 'date--end']):
                try:
                    title_elem = date_div.find('div', class_='date__title')
                    day_elem = date_div.find('div', class_='date__day')  
                    month_elem = date_div.find('div', class_='date__month')
                    
                    if all([title_elem, day_elem, month_elem]):
                        date_parts.append(f"{title_elem.get_text(strip=True)} {day_elem.get_text(strip=True)} {month_elem.get_text(strip=True)}")
                except:
                    continue
            
            date = ' '.join(date_parts)
            
            if link and link.startswith('/'):
                link = f"https://www.hackathon.com{link}"
            
            hackathons.append({'title': title, 'date': date, 'link': link})
        except:
            continue
    
    print(f"Hackathon.com: Found {len(hackathons)} hackathons")
    return hackathons


def fetch_all_hackathons():
    """Optimized multi-threaded scraping with improved concurrency"""
    print("Starting optimized multi-threaded hackathon scraping...")
    start_time = time.time()
    
    scrapers = [
        ("Devpost", scrape_devpost),
        ("Devfolio", scrape_devfolio), 
        ("MLH", scrape_mlh),
        ("Hackathon.com", scrape_hackathon_com)
    ]
    
    results = []
    
    # Optimized ThreadPoolExecutor with reduced workers for better resource usage
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:  # Reduced from 4
        future_to_scraper = {executor.submit(scraper_func): name 
                           for name, scraper_func in scrapers}
        
        for future in concurrent.futures.as_completed(future_to_scraper):
            scraper_name = future_to_scraper[future]
            try:
                scraper_results = future.result(timeout=180)  # Reduced from 300
                results.extend(scraper_results)
                elapsed = time.time() - start_time
                print(f"{scraper_name}: {len(scraper_results)} hackathons ({elapsed:.1f}s)")
            except Exception as e:
                print(f"{scraper_name} failed: {e}")
    
    # Ultra-fast deduplication using dict
    seen = {}
    unique = []
    duplicates = 0
    
    for h in results:
        key = f"{h.get('title', '')}{h.get('link', '')}"  # String concatenation is faster
        if key not in seen:
            seen[key] = True
            unique.append(h)
        else:
            duplicates += 1
    
    total_time = time.time() - start_time
    print(f"\nOptimized scraping complete!")
    print(f"Total: {len(unique)} unique hackathons ({duplicates} duplicates)")
    print(f"Runtime: {total_time:.1f}s ({len(unique)/total_time:.1f} hackathons/sec)")
    
    return unique


# Additional utility function for testing single scrapers
def test_single_scraper(scraper_name):
    """Test a single scraper for debugging"""
    scrapers = {
        'devpost': scrape_devpost,
        'devfolio': scrape_devfolio,
        'mlh': scrape_mlh,
        'hackathon': scrape_hackathon_com
    }
    
    if scraper_name.lower() in scrapers:
        print(f"Testing {scraper_name}...")
        start_time = time.time()
        results = scrapers[scraper_name.lower()]()
        end_time = time.time()
        print(f"{scraper_name}: {len(results)} hackathons in {end_time - start_time:.1f}s")
        return results
    else:
        print(f"Unknown scraper: {scraper_name}")
        return []


if __name__ == "__main__":
    start_time = time.time()
    all_hackathons = fetch_all_hackathons()
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.1f} seconds")
    print(f"Average: {len(all_hackathons) / (end_time - start_time):.1f} hackathons/second")