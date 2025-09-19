import time
import threading
import concurrent.futures
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def make_headless_driver():
    """Create a headless Chrome/Chromium driver that works both locally and in GitHub Actions."""

    opts = Options()
    opts.add_argument("--headless=new")  # modern headless mode
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--window-size=1920,1080")

    if os.getenv("GITHUB_ACTIONS") == "true":
        # On GitHub runners: use Chromium
        opts.binary_location = "/usr/bin/chromium-browser"
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        # Local dev: assumes Chrome is installed in PATH
        driver = webdriver.Chrome(options=opts)

    return driver


def _fast_scroll_devpost(driver):
    """Robust scrolling for Devpost until no new tiles appear."""
    print("Starting Devpost full scrolling...")

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "hackathon-tile"))
        )
    except:
        print("No hackathon tiles found on Devpost")
        return 0

    last_count = 0
    stagnant_rounds = 0
    max_stagnant = 8   # require stability across many rounds
    max_scrolls = 200  # allow deeper scrolls for full coverage

    for attempt in range(max_scrolls):
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.2)  # give time for new tiles to load

        tiles = driver.find_elements(By.CLASS_NAME, "hackathon-tile")
        new_count = len(tiles)

        if new_count > last_count:
            print(f"  Scroll {attempt+1}: {new_count} tiles (gained {new_count - last_count})")
            last_count = new_count
            stagnant_rounds = 0
        else:
            stagnant_rounds += 1
            print(f"  Scroll {attempt+1}: no new tiles ({stagnant_rounds}/{max_stagnant})")

        # Stop if stable for too long
        if stagnant_rounds >= max_stagnant:
            break

    print(f"Devpost scrolling finished with {last_count} tiles")
    return last_count


def _parse_devpost(soup):
    """Parse Devpost tiles into hackathon objects"""
    hackathons = []
    tiles = soup.find_all('div', class_='hackathon-tile')
    print(f"Parsing {len(tiles)} Devpost tiles...")

    for tile in tiles:
        try:
            title_tag = tile.find('h3')
            date_tag = tile.find('div', class_='submission-period')
            link_tag = tile.find('a', href=True)

            if not (title_tag and link_tag):
                continue

            title = title_tag.get_text(strip=True)
            date = date_tag.get_text(strip=True) if date_tag else ""
            link = link_tag['href']
            if link.startswith('/'):
                link = f"https://devpost.com{link}"

            hackathons.append({'title': title, 'date': date, 'link': link})
        except:
            continue

    print(f"Parsed {len(hackathons)} Devpost hackathons")
    return hackathons


def scrape_devpost():
    """Scrape Devpost with robust scrolling and parsing"""
    print("Starting Devpost scrape...")
    driver = make_headless_driver()
    try:
        driver.get('https://devpost.com/hackathons')
        time.sleep(2)

        _fast_scroll_devpost(driver)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    return _parse_devpost(soup)


def scrape_devfolio():
    """Optimized Devfolio scraping"""
    driver = make_headless_driver()
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
    driver = make_headless_driver()
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
    driver = make_headless_driver()
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