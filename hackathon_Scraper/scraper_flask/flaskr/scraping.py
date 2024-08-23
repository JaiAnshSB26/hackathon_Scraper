import requests
from bs4 import BeautifulSoup

# Define the URLs of the hackathon listings
websites = [
    "https://devfolio.co/hackathons",
    "https://devpost.com/hackathons",
    "https://www.hackerearth.com/challenges/",
    "https://www.eventbrite.com/d/online/hackathon/",
    "https://hackclub.com/events/"
]

def get_hackathons():
    list = [
        {"name": "Hackathon UW madison", "location": "madison", "participants": 169},
        {"name": "Hackathon UChicago", "location": "chicago", "participants": 369},
        {"name": "Hackathon EPFL", "location": "france", "participants": 569},
    ]
    responses = scrape_hackathon_sites(websites)
    #print(responses)
    return list

def scrape_hackathon_sites(websites):
    # Iterate through each website
    responses = []
    for url in websites:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        responses.append(soup.find_all('a'))
    return responses
        # Extract relevant hackathon details (e.g., title, date, prizes)
        # ...

        # Print or store the extracted information
        # ...

    # Repeat the process for other websites
    # Sample scraping code, gotta check html structure of pages to find popular ones