import requests
import json
import random
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

username = "OpenAI"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

nitter_instances = [
    "https://nitter.net",
    "https://nitter.cz",
    "https://nitter.privacydev.net",
    "https://nitter.it",
    "https://nitter.sethforprivacy.com"
]

def test_syndication():
    print("--- Testing Syndication ---")
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', id='__NEXT_DATA__')
            if script_tag:
                print("✅ Found __NEXT_DATA__")
            else:
                print("❌ Script tag not found.")
    except Exception as e:
        print(f"Error: {e}")

def test_nitter():
    print("\n--- Testing Nitter ---")
    instance = random.choice(nitter_instances)
    url = f"{instance}/{username}/rss"
    print(f"Trying instance: {instance}")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'xml')
            items = soup.find_all('item')
            print(f"✅ Found {len(items)} items in RSS.")
            if items:
                print(f"Latest title: {items[0].title.text if items[0].title else 'No title'}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_syndication()
    test_nitter()
