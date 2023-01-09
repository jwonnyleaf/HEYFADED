import os
import tweepy
import requests
import schedule
import time

from dotenv import load_dotenv

load_dotenv()

# Constants
CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_KEY_SECRET = os.environ["CONSUMER_KEY_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]
RIOT_API_KEY = os.environ["RIOT_API_KEY"]


# Twitter API Setup
auth = tweepy.OAuth1UserHandler(
    CONSUMER_KEY, CONSUMER_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
)
api = tweepy.API(auth)

# Obtains the PUUID
# summoner_request_link = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/Juice+On+Lime/?api_key={}".format(RIOT_API_KEY)
# summoner_response = requests.get(summoner_request_link)

# if summoner_response:
#     data = summoner_response.json()
#     puuid = data.get("puuid")
#     print(puuid)
# else:
#     print(f"Error : { summoner_response.text }")

# matches_request_link = "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?api_key={}".format(puuid, RIOT_API_KEY)
# matches_response = requests.get(matches_request_link)
# match_id = matches_response.json()[0]

# match_request_link = "https://americas.api.riotgames.com/lol/match/v5/matches/{}?api_key={}".format(match_id, RIOT_API_KEY)
# match_response = requests.get(match_request_link)

def job():
    api.update_status("10 MINUTES TEST")
    print("TWEETED")

schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
