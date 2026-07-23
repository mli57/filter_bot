import requests
import json
from dotenv import load_dotenv
import os

load_dotenv("token.env") # no-op in CI, where BOT_TOKEN comes from the repo secret
BOT_TOKEN = os.environ["BOT_TOKEN"]

SPEEDY_CHANNEL_ID = "1529666742400323674" # id of speedyapply channel
SPEEDY_ID = "1528605281167085666"
CANADA_CHANNEL_ID = "1529658963455508541"

CANADA_KEYWORDS = ["canada", "toronto", "vancouver", "montreal", "ottawa", "calgary", "edmonton", "winnipeg"]


## Helper funcs
# returns the embed's fields, or None if this message isn't a job post, in case a normal message gets sent
def get_fields(message):
    embeds = message.get("embeds") or []
    if not embeds:
        return None
    return embeds[0].get("fields") or None

def get_field_value(fields, name):
    for field in fields:
        if field["name"] == name:
            return field["value"]
    return None

# Check if each location is canadian by comparing it to a list of keywords
def is_canada(location):
    location_lower = location.lower()
    return any(keyword in location_lower for keyword in CANADA_KEYWORDS)


## Load & save files
# open file f and wipes the old id, dump dict of new id into it
def save_last_seen_id(new_id):
    with open("last_seen_id.json", "w") as f:
        json.dump({"last_seen_id": new_id}, f)

# returns None on the first ever run, when the file is missing, empty or malformed
def load_last_seen_id():
    try:
        with open("last_seen_id.json", "r") as f:
            return json.load(f)["last_seen_id"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


## Pipeline
# fetch the latest batch of messages from the speedyapply channel
def fetch_messages():
    url = f"https://discord.com/api/v10/channels/{SPEEDY_CHANNEL_ID}/messages?limit=100"
    resp = requests.get(url, headers={"Authorization": f"Bot {BOT_TOKEN}"})
    resp.raise_for_status() # if error occurs a 401/429 returns a dict, not a list, and breaks the loop below
    return resp.json()

# return only new posts by comparing post ID to the latest post id from the last scrape
def filter_recent_posts(messages, last_seen_id):
    recent_jobs = []
    for message in messages:
        if int(message["id"]) <= int(last_seen_id): # newer posts always have numerically larger id
            break
        else:
            recent_jobs.append(message)
    return recent_jobs

# Get .json version of each post made in the last hour and return a list of canadian specific ones
def filter_canada_posts(messages):
    canada_jobs = []
    for message in messages:
        if message["author"]["id"] == SPEEDY_ID:
            fields = get_fields(message)
            if fields is None: # not a job post, skip it rather than crashing the run
                continue
            for field in fields:
                if field["name"] == "Location" and is_canada(field["value"]):
                    canada_jobs.append(message)
    return canada_jobs

# builds new posts and post them
def post_canadian_jobs(canada_jobs):
    url = f"https://discord.com/api/v10/channels/{CANADA_CHANNEL_ID}/messages"
    for message in canada_jobs: # get the specific link to the job, and its location
        fields = get_fields(message)
        job = get_field_value(fields, "Job")
        location = get_field_value(fields, "Location")
        message_text = f"{job}\nLocation: {location}"

        resp = requests.post(url, headers={"Authorization": f"Bot {BOT_TOKEN}"}, json={"content": message_text})
        resp.raise_for_status() # a rejected post must stop the run, so the marker doesn't advance past it


## Entry point
def main():
    messages = fetch_messages()
    if not messages:
        return

    last_seen_id = load_last_seen_id()
    if last_seen_id is None: # first run: mark where we are, start posting next time
        save_last_seen_id(messages[0]["id"])
        return

    recent = filter_recent_posts(messages, last_seen_id)
    if not recent:
        return

    post_canadian_jobs(filter_canada_posts(recent))
    save_last_seen_id(recent[0]["id"]) # only advance once the posting has gone through

if __name__ == "__main__":
    main()
