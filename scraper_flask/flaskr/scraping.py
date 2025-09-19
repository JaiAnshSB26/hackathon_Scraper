import os
import time
import json
import traceback
import concurrent.futures
from typing import List, Dict

from bs4 import BeautifulSoup
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager
    _HAS_WM = True
except Exception:
    _HAS_WM = False

OUTPUT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "hackathons.json"
)
GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)


def _log(*args, **kwargs):
    print(*args, **kwargs, flush=True)


def _safe_get_text(el):
    return el.get_text(strip=True) if el else ""

def make_headless_driver() -> webdriver.Chrome:
    """Return a configured headless Chrome/Chromium webdriver for local / CI usage."""
    opts = Options()

    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-background-timer-throttling")
    opts.add_argument("--disable-renderer-backgrounding")
    opts.add_argument(f"--user-agent={DEFAULT_USER_AGENT}")

    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    prefs = {
        "profile.default_content_setting_values.images": 2,  # don't load images
        "profile.default_content_setting_values.media_stream": 2,
    }
    opts.add_experimental_option("prefs", prefs)

    if GITHUB_ACTIONS:
        chromium_possible_binaries = [
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
        ]
        binary = next((p for p in chromium_possible_binaries if os.path.exists(p)), None)
        if binary:
            opts.binary_location = binary

        chromedriver_paths = ["/usr/bin/chromedriver", "/usr/local/bin/chromedriver"]
        driver_path = next((p for p in chromedriver_paths if os.path.exists(p)), None)
        if driver_path:
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=opts)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(1)
            return driver
        else:
            _log("Warning: chromedriver not found at typical paths in CI; falling back to webdriver_manager.")
   
    if _HAS_WM:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(1)
    return driver

def wait_for_css(driver, css_selector, timeout=12):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
    )


def scroll_to_bottom(driver, pause=1.0, max_scrolls=60, stop_if_no_change=4):
    """Scroll the page to load lazy content. Returns True if scrolled at least once."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    stagnation = 0
    scrolled = False
    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            stagnation += 1
        else:
            scrolled = True
            stagnation = 0
            last_height = new_height
        if stagnation >= stop_if_no_change:
            break
    return scrolled


def scrape_devpost() -> List[Dict]:
    _log("Starting Devpost scrape...")
    driver = None
    try:
        driver = make_headless_driver()
        driver.get("https://devpost.com/hackathons")

        try:
            wait_for_css(driver, ".hackathon-tile", timeout=12)
        except Exception:
            _log("Devpost: no immediate tiles; continuing to scroll/wait")
        scroll_to_bottom(driver, pause=0.9, max_scrolls=100, stop_if_no_change=5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        results = []
        for tile in soup.select("div.hackathon-tile"):
            try:
                title = _safe_get_text(tile.select_one("h3.mb-4"))
                date = _safe_get_text(tile.select_one("div.submission-period"))
                link_tag = tile.select_one("a.flex-row")
                link = link_tag.get("href") if link_tag else ""
                if link and link.startswith("/"):
                    link = "https://devpost.com" + link
                if title:
                    results.append({"title": title, "date": date, "link": link})
            except Exception:
                continue
        _log(f"Devpost: found {len(results)} items")
        return results
    except Exception as e:
        _log("Devpost failed:", e)
        _log(traceback.format_exc())
        return []
    finally:
        if driver:
            driver.quit()


def scrape_devfolio() -> List[Dict]:
    """Scrape Devfolio by loading the public page with Selenium (GraphQL blocked in CI)."""
    _log("Starting Devfolio scrape (Selenium)...")
    driver = None
    try:
        driver = make_headless_driver()
        driver.get("https://devfolio.co/hackathons")
        try:
            wait_for_css(driver, "div", timeout=10) 
        except:
            pass

        scroll_to_bottom(driver, pause=1.0, max_scrolls=80, stop_if_no_change=5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        results = []

        for a in soup.select("a"):
            try:
                href = a.get("href", "")
                if "/hackathons/" in href or href.startswith("/h/") or "devfolio.co/hackathons" in href:
                    title = _safe_get_text(a.select_one("h3") or a)
                    link = href if href.startswith("http") else ("https://devfolio.co" + href)
                    if title:
                        results.append({"title": title, "date": "", "link": link})
            except Exception:
                continue

        seen = set()
        uniq = []
        for r in results:
            key = (r.get("title", "").strip(), r.get("link", ""))
            if key not in seen:
                seen.add(key)
                uniq.append(r)
        _log(f"Devfolio: found {len(uniq)} items (heuristic)")
        return uniq
    except Exception as e:
        _log("Devfolio failed:", e)
        _log(traceback.format_exc())
        return []
    finally:
        if driver:
            driver.quit()


def scrape_mlh() -> List[Dict]:
    """Scrape MLH by loading page and waiting for event cards to render."""
    _log("Starting MLH scrape (Selenium)...")
    driver = None
    try:
        driver = make_headless_driver()
        driver.get("https://mlh.io/seasons/2025/events")
        try:
            wait_for_css(driver, ".event", timeout=12)
        except Exception:
            _log("MLH: .event not present immediately, will scroll/wait")
        scroll_to_bottom(driver, pause=1.0, max_scrolls=80, stop_if_no_change=5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        results = []
        for ev in soup.select("div.event"):
            try:
                title = _safe_get_text(ev.select_one("h3.event-name"))
                date = _safe_get_text(ev.select_one("p.event-date"))
                a = ev.select_one("a.event-link")
                link = a.get("href") if a else ""
                if link and link.startswith("/"):
                    link = "https://mlh.io" + link
                if title:
                    results.append({"title": title, "date": date, "link": link})
            except Exception:
                continue
        _log(f"MLH: found {len(results)} items")
        if not results:
            try:
                _log("MLH: trying JSON feed fallback with browser-like headers...")
                headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
                resp = requests.get("https://mlh.io/seasons/2025/events.json", headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                results = []
                for ev in data.get("events", []):
                    results.append({
                        "title": ev.get("name"),
                        "date": f"{ev.get('start_date')} → {ev.get('end_date')}",
                        "link": ev.get("event_link")
                    })
                _log(f"MLH JSON feed: found {len(results)} items")
            except Exception as e_json:
                _log("MLH JSON fallback failed:", e_json)
        return results
    except Exception as e:
        _log("MLH failed:", e)
        _log(traceback.format_exc())
        return []
    finally:
        if driver:
            driver.quit()


def scrape_hackathon_com() -> List[Dict]:
    _log("Starting Hackathon.com scrape...")
    driver = None
    try:
        driver = make_headless_driver()
        driver.get("https://www.hackathon.com/online")
        try:
            wait_for_css(driver, ".ht-eb-card", timeout=10)
        except:
            _log("Hackathon.com: no immediate cards; scrolling...")
        scroll_to_bottom(driver, pause=1.0, max_scrolls=80, stop_if_no_change=5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        results = []
        for card in soup.select("div.ht-eb-card"):
            try:
                title_tag = card.select_one("a.ht-eb-card__title")
                if not title_tag:
                    continue
                title = _safe_get_text(title_tag)
                link = title_tag.get("href") or ""
                if link and link.startswith("/"):
                    link = "https://www.hackathon.com" + link
                # build date strings (fallback if unavailable)
                date_parts = []
                for date_div in card.select("[class*='date--']"):
                    date_parts.append(_safe_get_text(date_div))
                date = " ".join(date_parts)
                results.append({"title": title, "date": date, "link": link})
            except Exception:
                continue
        _log(f"Hackathon.com: found {len(results)} items")
        return results
    except Exception as e:
        _log("Hackathon.com failed:", e)
        _log(traceback.format_exc())
        return []
    finally:
        if driver:
            driver.quit()

def fetch_all_hackathons() -> List[Dict]:
    _log("Starting multi-threaded scrape (prod-ready)...")
    start = time.time()

    tasks = [
        ("Devpost", scrape_devpost),
        ("Devfolio", scrape_devfolio),
        ("MLH", scrape_mlh),
        ("Hackathon.com", scrape_hackathon_com),
    ]

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        future_to_name = {ex.submit(func): name for name, func in tasks}
        for fut in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[fut]
            try:
                res = fut.result(timeout=240)
                results.extend(res or [])
                _log(f"{name}: {len(res or [])} items")
            except Exception as e:
                _log(f"{name} failed during run: {e}")
                _log(traceback.format_exc())

    seen = set()
    unique = []
    for h in results:
        key = (h.get("title", "").strip(), (h.get("link") or "").strip())
        if key not in seen:
            seen.add(key)
            unique.append(h)

    elapsed = time.time() - start
    _log(f"\nTotal unique hackathons: {len(unique)} (elapsed: {elapsed:.1f}s)")

    try:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(unique, f, ensure_ascii=False, indent=2)
        _log(f"Written {len(unique)} hackathons to {OUTPUT_FILE}")
    except Exception as e:
        _log("Failed to write output file:", e)
        _log(traceback.format_exc())

    return unique

if __name__ == "__main__":
    all_hacks = fetch_all_hackathons()
    _log(f"Fetched {len(all_hacks)} hackathons total.")
