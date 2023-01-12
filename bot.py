import os
import tweepy
import requests
import schedule
import time
import pytz
import datetime
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

# Initialize Database
db_client = MongoClient(CLUSTER)
db = db_client.heyfaded

VALID_USERS = [user["summoner_name"] for user in db.valid_users.find()]

# Twitter API Setup
auth = tweepy.OAuth1UserHandler(
    CONSUMER_KEY, CONSUMER_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
)
api = tweepy.API(auth)


def retrieveLastMatchID(summoner_name):
    # Obtains the PUUID
    summoner_request_link = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{}/?api_key={}".format(
        summoner_name, RIOT_API_KEY
    )
    summoner_response = requests.get(summoner_request_link)

    # If there data for the summoner name then grab their ID, else print an error.
    if summoner_response:
        data = summoner_response.json()
        puuid = data.get("puuid")
    else:
        print(f"[Error] : { summoner_response.text }")

    # Obtain the Match ID and return
    matches_request_link = "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?api_key={}".format(
        puuid, RIOT_API_KEY
    )
    matches_response = requests.get(matches_request_link)
    match_id = matches_response.json()[0]
    return match_id


def retrieveMatchInfo(match_id):
    # Send a request to Riot API to grab the data from the match given the ID
    match_request_link = (
        "https://americas.api.riotgames.com/lol/match/v5/matches/{}?api_key={}".format(
            match_id, RIOT_API_KEY
        )
    )
    match_response = requests.get(match_request_link).json()
    # Insert match meta data (identification) into database
    db.matches.insert_one(match_response["metadata"])
    match_info = [
        x
        for x in match_response["info"]["participants"]
        if x["summonerName"] in VALID_USERS
    ]

    user_data = []
    for user in match_info:
        user_data.append(
            {
                "summoner_name": user["summonerName"],
                "win_status": "won" if user["win"] else "lost",
                "gamemode": match_response["info"]["gameMode"],
                "game_time": round(user["challenges"]["gameLength"] / 60, 2),
                "kda": round(user["challenges"]["kda"], 2),
                "champion": user["championName"],
            }
        )
    return user_data


def leagueChecker():
    """The Main Driver of the League of Legends Twitter Updates"""
    valid_users_list = VALID_USERS
    for user in valid_users_list:
        match_id = retrieveLastMatchID(user)
        if db.matches.count_documents({"matchId": match_id}, limit=1) > 0:
            print(f"[Error]: {user}'s match: {match_id} has already been tweeted")
        else:
            info = retrieveMatchInfo(match_id)

            if(len(info) > 1):
                qty = "few summoners have"
            else:
                qty = "summoner has"

            win_status = info[0]["win_status"]
            gamemode = info[0]["gamemode"]
            game_time = info[0]["game_time"]

            stats = ""
            for summoner in info:
                stats += "\n\t\t{} ended the game with a {} KDA on {}".format(
                    summoner["summoner_name"],
                    summoner["kda"],
                    summoner["champion"],
                )

            tweet_time = datetime.datetime.now(pytz.timezone("US/Central")).strftime("%Y/%m/%d %I:%M %p")
            tweet = (
            f"""☁︎ FADED UPDATE ☁︎

            A {qty} just {win_status} a game of {gamemode} in {game_time} minutes.\n{stats}\n\n[{tweet_time}]
            """
            )
            
            api.update_status(tweet)
            print(tweet)


schedule.every(1).minutes.do(leagueChecker)

while True:
    schedule.run_pending()
    time.sleep(1)