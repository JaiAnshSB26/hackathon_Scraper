import os
import time
import concurrent.futures
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def make_headless_driver():
    """Create a headless Chrome/Chromium driver that works both locally and in GitHub Actions."""

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--window-size=1920,1080")

    if os.getenv("GITHUB_ACTIONS") == "true":
        opts.binary_location = "/usr/bin/chromium-browser"
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)

    return driver

def _fast_scroll_devpost(driver):
    """Scroll until all hackathons are loaded on Devpost."""
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "hackathon-tile"))
    )
    time.sleep(1)

    last_height = driver.execute_script("return document.body.scrollHeight")
    stagnant = 0
    tiles = set()

    while stagnant < 5:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

        new_height = driver.execute_script("return document.body.scrollHeight")
        new_tiles = driver.find_elements(By.CLASS_NAME, "hackathon-tile")

        if len(new_tiles) > len(tiles):
            tiles = set(new_tiles)
            stagnant = 0
        else:
            stagnant += 1

        if new_height == last_height:
            stagnant += 1
        last_height = new_height

    return tiles


def scrape_devpost():
    print("Scraping Devpost...")
    driver = make_headless_driver()
    try:
        driver.get("https://devpost.com/hackathons")
        tiles = _fast_scroll_devpost(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    hackathons = []
    for tile in soup.find_all("div", class_="hackathon-tile"):
        try:
            title_tag = tile.find("h3", class_="mb-4")
            date_tag = tile.find("div", class_="submission-period")
            link_tag = tile.find("a", class_="flex-row")

            if not (title_tag and date_tag and link_tag):
                continue

            title = title_tag.get_text(strip=True)
            date = date_tag.get_text(strip=True)
            link = link_tag.get("href")
            if link.startswith("/"):
                link = f"https://devpost.com{link}"

            hackathons.append({"title": title, "date": date, "link": link})
        except Exception:
            continue

    print(f"Devpost: {len(hackathons)} hackathons")
    return hackathons


# -----------------------
# Devfolio (GraphQL API)
# -----------------------
def scrape_devfolio():
    print("Scraping Devfolio API...")
    url = "https://api.devfolio.co/api/graphql"

    query = """
    query {
      hackathons(type: "current", limit: 1000) {
        title
        slug
        starts_at
        ends_at
      }
    }
    """

    try:
        resp = requests.post(url, json={"query": query}, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        hackathons = []
        for h in data["data"]["hackathons"]:
            link = f"https://devfolio.co/hackathons/{h['slug']}"
            date = f"{h['starts_at']} → {h['ends_at']}"
            hackathons.append({"title": h["title"], "date": date, "link": link})

        print(f"Devfolio: {len(hackathons)} hackathons")
        return hackathons

    except Exception as e:
        print(f"Devfolio API failed: {e}")
        return []


def scrape_mlh():
    print("Scraping MLH API...")
    url = "https://mlh.io/seasons/2025/events.json"

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        hackathons = []
        for event in data.get("events", []):
            hackathons.append(
                {
                    "title": event.get("name"),
                    "date": f"{event.get('start_date')} → {event.get('end_date')}",
                    "link": event.get("event_link"),
                }
            )

        print(f"MLH: {len(hackathons)} hackathons")
        return hackathons

    except Exception as e:
        print(f"MLH API failed: {e}")
        return []

def scrape_hackathon_com():
    print("Scraping Hackathon.com...")
    driver = make_headless_driver()
    try:
        driver.get("https://www.hackathon.com/online")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    hackathons = []
    for card in soup.find_all("div", class_="ht-eb-card"):
        try:
            title_tag = card.find("a", class_="ht-eb-card__title")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href")
            if link.startswith("/"):
                link = f"https://www.hackathon.com{link}"

            dates = card.find_all("div", class_=["date--start", "date--end"])
            date_strs = []
            for d in dates:
                title_elem = d.find("div", class_="date__title")
                day_elem = d.find("div", class_="date__day")
                month_elem = d.find("div", class_="date__month")
                if title_elem and day_elem and month_elem:
                    date_strs.append(
                        f"{title_elem.get_text(strip=True)} {day_elem.get_text(strip=True)} {month_elem.get_text(strip=True)}"
                    )
            date = " ".join(date_strs)

            hackathons.append({"title": title, "date": date, "link": link})
        except Exception:
            continue

    print(f"Hackathon.com: {len(hackathons)} hackathons")
    return hackathons

def fetch_all_hackathons():
    print("Starting multi-source scraping...")
    start = time.time()

    scrapers = [
        ("Devpost", scrape_devpost),
        ("Devfolio", scrape_devfolio),
        ("MLH", scrape_mlh),
        ("Hackathon.com", scrape_hackathon_com),
    ]

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_name = {executor.submit(func): name for name, func in scrapers}
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            try:
                data = future.result()
                results.extend(data)
            except Exception as e:
                print(f"{name} failed: {e}")

    seen = set()
    unique = []
    for h in results:
        key = f"{h.get('title')}|{h.get('link')}"
        if key not in seen:
            seen.add(key)
            unique.append(h)

    elapsed = time.time() - start
    print(f"\nScraping complete: {len(unique)} unique hackathons in {elapsed:.1f}s")
    return unique


if __name__ == "__main__":
    all_hacks = fetch_all_hackathons()
    print(f"Fetched {len(all_hacks)} hackathons total.")
