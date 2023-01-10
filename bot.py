import os
import tweepy
import requests
import schedule
import time
from pymongo import MongoClient

from dotenv import load_dotenv

load_dotenv()

# Constants
CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_KEY_SECRET = os.environ["CONSUMER_KEY_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]
RIOT_API_KEY = os.environ["RIOT_API_KEY"]
CLUSTER = "mongodb+srv://fadeddevs:{}@cluster0.awnzdcd.mongodb.net/?retryWrites=true&w=majority".format(
    os.environ["DB_PASS"]
)
VALID_USERS = ["Juice On Lime", "Consistencies", "Bryan Le Tran", "Mid Is Home"]

# Initialize Database
db_client = MongoClient(CLUSTER)
db = db_client.heyfaded

# Twitter API Setup
auth = tweepy.OAuth1UserHandler(
    CONSUMER_KEY, CONSUMER_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
)
api = tweepy.API(auth)

def retrieveLastMatch():
    # Obtains the PUUID
    summoner_request_link = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/Juice+On+Lime/?api_key={}".format(
        RIOT_API_KEY
    )
    summoner_response = requests.get(summoner_request_link)

    if summoner_response:
        data = summoner_response.json()
        puuid = data.get("puuid")
    else:
        print(f"[Error] : { summoner_response.text }")

    # Obtain the most recent match
    matches_request_link = "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?api_key={}".format(
        puuid, RIOT_API_KEY
    )
    matches_response = requests.get(matches_request_link)
    match_id = matches_response.json()[0]

    if(db.matches.count_documents({"matchId": match_id}, limit = 1) > 0):
        print("[Error]: Already Tweeted Match")
        return

    match_request_link = (
        "https://americas.api.riotgames.com/lol/match/v5/matches/{}?api_key={}".format(
            match_id, RIOT_API_KEY
        )
    )

    match_response = requests.get(match_request_link).json()
    db.matches.insert_one(match_response["metadata"])
    match_data = [
        x
        for x in match_response["info"]["participants"]
        if x["summonerName"] in VALID_USERS
    ]

    for user in match_data:
        user_data = {
            "summonerName": user["summonerName"],
            "winStatus": "won" if user["win"] else "lost",
            "gameTime": round(user["challenges"]["gameLength"] / 60, 2),
            "kda": round(user["challenges"]["kda"], 2),
            "champion": user["championName"],
        }
        tweet = (
            """[FADED UPDATE] 

            Summoner: {summonerName} has just {winStatus} on the rift.
            
            The User finished in {gameTime} minutes with a {kda} KDA on {champion}.
            """.format(
                summonerName=user_data["summonerName"],
                winStatus=user_data["winStatus"],
                gameTime=user_data["gameTime"],
                kda=user_data["kda"],
                champion=user_data["champion"],
            )
        )
        api.update_status(tweet)


schedule.every(1).minutes.do(retrieveLastMatch)

while True:
    schedule.run_pending()
    time.sleep(1)
