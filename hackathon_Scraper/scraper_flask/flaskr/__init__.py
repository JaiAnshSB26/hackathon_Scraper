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
        # Setup Chrome WebDriver with ChromeDriverManager to automatically handle driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get('https://devpost.com/hackathons')

        # Wait for the page to load completely
        time.sleep(5)  # Adjust as needed

        # Get the page source and pass it to BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        # Print the HTML for debugging
        print(soup.prettify())

        # Locate and extract hackathon data
        hackathons = []
        hackathon_tiles = soup.find_all('div', class_='hackathon-tile')

        if not hackathon_tiles:
            print("No hackathon tiles found!")
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

        print(hackathons)

        return render_template('hackathons.html', hackathons=hackathons)

    return app
