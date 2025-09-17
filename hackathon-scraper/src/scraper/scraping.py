import os
import json
import time
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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.set_page_load_timeout(15)
    driver.implicitly_wait(2)
    return driver

def scrape_devpost():
    driver = _make_headless_driver()
    try:
        driver.get('https://devpost.com/hackathons')
        time.sleep(1.5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    hackathons = []
    for tile in soup.find_all('div', class_='hackathon-tile'):
        title = tile.find('h3', class_='mb-4').get_text(strip=True)
        date = tile.find('div', class_='submission-period').get_text(strip=True)
        link = tile.find('a', class_='flex-row')['href']
        hackathons.append({'title': title, 'date': date, 'link': link})

    return hackathons

def fetch_all_hackathons():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(scrape_devpost)
        devpost_hackathons = future.result()

    all_hackathons = devpost_hackathons
    return all_hackathons

def save_hackathons_to_json(hackathons):
    with open(os.path.join('data', 'hackathons.json'), 'w') as f:
        json.dump(hackathons, f, indent=4)

if __name__ == "__main__":
    hackathons = fetch_all_hackathons()
    save_hackathons_to_json(hackathons)