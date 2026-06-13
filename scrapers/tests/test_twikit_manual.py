from twikit import Client
import json
import traceback

def main():
    print("🚀 Initializing Twikit Client (Sync)...")
    client = Client('en-US')
    
    with open('scrapers/cookies.json', 'r') as f:
        cookies = json.load(f)
        client.set_cookies(cookies)
        
    print("🍪 Cookies loaded. Fetching user @OpenAI...")
    try:
        user = client.get_user_by_screen_name('OpenAI')
        print(f"✅ Successfully found user. Name: {user.name}, ID: {user.id}")
        print("Fetching latest 2 tweets...")
        tweets = client.get_user_tweets(user.id, 'Tweets', count=2)
        for t in tweets:
            print(f"--- Tweet ID: {t.id} ---")
            print(f"Text: {t.text}")
    except Exception as e:
        print(f"❌ Error during fetch: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
