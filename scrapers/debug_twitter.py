import requests
import json
from bs4 import BeautifulSoup

url = "https://syndication.twitter.com/srv/timeline-profile/screen-name/OpenAI"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")

soup = BeautifulSoup(response.text, 'html.parser')
script_tag = soup.find('script', id='__NEXT_DATA__')

if script_tag:
    data = json.loads(script_tag.string)
    timeline = data.get('props', {}).get('pageProps', {}).get('timeline', {}).get('entries', [])
    print(f"Found {len(timeline)} entries in timeline.")
    if len(timeline) > 0:
        first_tweet = timeline[0].get('content', {}).get('tweet', {})
        print(f"First tweet ID: {first_tweet.get('id_str')}")
        print(f"First tweet text: {first_tweet.get('full_text')[:50]}...")
else:
    print("Could not find __NEXT_DATA__ script tag.")
    print("Response snippet:", response.text[:500])
