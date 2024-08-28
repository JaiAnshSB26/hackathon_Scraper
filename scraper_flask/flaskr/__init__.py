import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from flask import Flask, render_template


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/hello')
    def hello():
        return render_template('index.html')

    @app.route("/hackathons")
    def hackathons_api():
        hackathons = scraping.get_hackathons()
        return hackathons

    @app.route('/')
    def index():
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get('https://devpost.com/hackathons')

        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        #print(soup.prettify())

        hackathons = []
        hackathon_tiles = soup.find_all('div', class_='hackathon-tile')

        if not hackathon_tiles:
            print("No hackathon tiles found")
            return render_template('hackathons.html', hackathons=[])

        for hackathon in hackathon_tiles:
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
                print("Skipping a hackathon due to missing data:", hackathon)

        getHackathons(hackathons)
        getmlhHackathons(hackathons)
        getMoreHackathons(hackathons)

        #print(hackathons)
        return render_template('hackathons.html', hackathons=hackathons)

    return app

    def getHackathons(hackathons):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get('https://devfolio.co/hackathons')
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        hackathon_group = soup.find_all('div', class_='sc-fmGnzW')
        for hackathon in hackathon_group:
            link_tag = hackathon.find('a', class_ = 'lkflLS') #text confusing, try 1 instead of l in case of error
            date_tag = hackathon.find('p', class_ = 'cqgLqk')
            title_tag = hackathon.find('h3', class_ = 'sc-dkzDqf')
            if title_tag and date_tag and link_tag:
                title = title_tag.text.strip()
                date = date_tag.text.strip()
                link = link_tag['href']
                if link.startswith('/'):
                    link = f"https://devfolio.com{link}"
                hackathons.append({'title': title, 'date': date, 'link': link})
            else:
                print("Skipping a hackathon due to missing data:", hackathon)

    def getmlhHackathons(hackathons):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get('https://mlh.io/seasons/2025/events')
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
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
                    link = f"https://https://mlh.io/seasons/2025/events{link}"
                hackathons.append({'title': title, 'date': date, 'link': link})
            else:
                print("Skipping a hackathon due to missing data:", hackathon)

    def getMoreHackathons(hackathons):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get('https://www.hackathon.com/online')
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        all_hackathons = soup.find_all('div', class_='ht-eb-card')
        for hackathon in all_hackathons:
            title_tag = hackathon.find('a', class_='ht-eb-card__title')
            link_tag = hackathon.find('a', class_='ht-eb-card__title')
            date = ''
            start_date = hackathon.find('div', class_='date--start')
            date += start_date.find('div', class_='date__title')
            date += ' '
            date += start_date.find('div', class_='date__day')
            date += ' '
            date += start_date.find('div', class_='date__month')
            end_date = hackathon.find('div', class_='date--end')
            date += end_date.find('div', class_='date__title')
            date += ' '
            date += end_date.find('div', class_='date__day')
            date += ' '
            date += end_date.find('div', class_='date__month')
            if title_tag and link_tag:
                title = title_tag.text.strip()
                link = link_tag['href']
                if link.startswith('/'):
                    link = f"https://www.hackathon.com/online{link}"
                hackathons.append({'title': title, 'date': date, 'link': link})
            else:
                print("Skipping a hackathon due to missing data:", hackathon)
