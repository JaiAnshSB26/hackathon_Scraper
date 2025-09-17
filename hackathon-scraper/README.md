# README.md

# Hackathon Scraper

## Overview
The Hackathon Scraper is a project designed to fetch and display hackathon data from various sources. It features a static front end that presents the scraped data and utilizes GitHub Actions for automated scraping every 24 hours.

## Project Structure
```
hackathon-scraper
├── .github
│   └── workflows
│       └── daily-scrape.yml
├── src
│   ├── scraper
│   │   ├── __init__.py
│   │   └── scraping.py
│   └── static
│       ├── index.html
│       ├── style.css
│       └── script.js
├── data
│   └── hackathons.json
├── requirements.txt
├── build.py
└── README.md
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/hackathon-scraper.git
   cd hackathon-scraper
   ```

2. **Install Dependencies**
   Ensure you have Python and pip installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Scraper Manually**
   You can run the scraper manually by executing:
   ```bash
   python src/scraper/scraping.py
   ```

4. **Deploying the Static Front End**
   The static front end is located in the `src/static` directory. You can serve it using any static file server or deploy it to GitHub Pages.

## GitHub Actions
The project includes a GitHub Actions workflow located at `.github/workflows/daily-scrape.yml` that automates the scraping process every 24 hours. Ensure that your GitHub repository is set up to run this workflow.

## Usage
After the scraping process runs, the scraped data will be saved in `data/hackathons.json`. The static front end will read this data and display it to users.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.