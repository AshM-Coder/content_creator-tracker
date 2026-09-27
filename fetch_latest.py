# Loading packages 
import os
import csv
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

# Read the API key from the .env file
# External user need to generate thier own API key and .env file look at .env example for details
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"

# YouTube handles for 5 content creators selected
HANDLES = ["jasmineandtea", "TheCarolinaLifestyle", "lenalifts", "DrFayeBate", "cuppabeans"]

# File where each run's numbers get logged and growth data since last run
SNAPSHOT_FILE ='snapshot.csv'
GROWTH_FILE = "growth.csv"

# Send request to youtube and return the answer as a Python dict
def call_api(endpoint, params):
    params = {**params, "key": API_KEY}
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()

# Convert numbers to integers keep none
def to_int(value):
    if value is None: 
        return None
    return int(value)

# Get channels from youtube if it does not exist just keep none
def get_channel(handle):
    data= call_api("channels", {"part": "snippet, statistics,contentDetails", "forHandle": handle},)
    items = data.get("items",[])
    if not items: 
        return None
    return items[0]

# Get the uploads playlist (newest first)
def get_uploads_playlist_id(channel):
    return channel["contentDetails"]["relatedPlaylists"]["uploads"]

# Pull the most recent item from the playlist
def get_latest_video(uploads_playlist_id):
    data= call_api("playlistItems", {"part":"snippet", "playlistId": uploads_playlist_id, "maxResults":1,})
    items=data.get("items",[])
    if not items:
        return None
    snippet = items[0]['snippet']
    return{'video_id':snippet['resourceId']['videoId'], 'title':snippet['title'], 'published_at':snippet['publishedAt'],} 

# Get the viewers count from this latest video
def get_video_stats(video_id):
    data = call_api("videos", {"part": "statistics", "id": video_id})
    items = data.get("items", [])
    if not items:
        return None
    return items[0]["statistics"]

# Previous numbers to comapre the numbers generated now against
def get_previous_snapshot(handle):
    if not os.path.exists(SNAPSHOT_FILE):
        return None
    with open(SNAPSHOT_FILE, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["handle"] == handle]
    if not rows:
        return None
    rows.sort(key=lambda r: r["timestamp"])
    return rows[-1] 

# Append this run's numbers as one new row 
def append_snapshot(row):
    file_exists = os.path.exists(SNAPSHOT_FILE)
    with open(SNAPSHOT_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# Subtract last snapshot's numbers from today's, field by field
def compute_growth(previous, current):
    if previous is None:
        return None
    fields = ("subscriber_count", "channel_view_count", "latest_video_views", "latest_video_likes")
    growth = {}
    for field in fields:
        prev_val, curr_val = previous.get(field), current.get(field)
        if prev_val in (None, "") or curr_val is None:
            growth[field] = None
        else:
            growth[field] = curr_val - int(prev_val)
    return growth

def append_growth(handle, name, timestamp, growth):
    if growth is None:
        return   # first run for this creator so nothing to compare yet, so SKIP
    row = {"timestamp": timestamp,"handle": handle,"name": name,
        "subscriber_growth": growth["subscriber_count"],
        "channel_view_growth": growth["channel_view_count"],
        "latest_video_view_growth": growth["latest_video_views"],
        "latest_video_like_growth": growth["latest_video_likes"],}
    file_exists = os.path.exists(GROWTH_FILE)
    with open(GROWTH_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# Loop over all the handles and give results
def main():
    if not API_KEY:
        print("Missing YOUTUBE_API_KEY — check your .env file")
        return

    for handle in HANDLES:
        channel = get_channel(handle)
        if channel is None:
            print(f"{handle}: channel not found")
            continue
        name = channel["snippet"]["title"]
        subs = to_int(channel["statistics"].get("subscriberCount"))
        channel_views = to_int(channel["statistics"].get("viewCount"))   
        uploads_playlist = get_uploads_playlist_id(channel)
        latest = get_latest_video(uploads_playlist)
        if latest is None:
            print(f"{name} (@{handle}): no uploads found")
            continue
        video_stats = get_video_stats(latest["video_id"]) or {}
        views = to_int(video_stats.get("viewCount"))
        likes = to_int(video_stats.get("likeCount"))                    
        current = {"timestamp": datetime.now(timezone.utc).isoformat(),
            "handle": handle, "name": name, "subscriber_count": subs,
            "channel_view_count": channel_views, "latest_video_id": latest["video_id"],
            "latest_video_views": views, "latest_video_likes": likes,}
        previous = get_previous_snapshot(handle)   
        growth = compute_growth(previous, current) 
        previous = get_previous_snapshot(handle)
        growth = compute_growth(previous, current)
        append_growth(handle, name, current["timestamp"], growth)   
        print(f"{name} (@{handle}) — {subs:,} subs" if subs else f"{name} (@{handle})")
        print(f"  Latest: {latest['title']}")
        print(f"  Views: {views:,} | Likes: {likes:,}" if views and likes else "  Views/likes: n/a")
        if growth:                                  
            print(f"  Since last run: subs {growth['subscriber_count']:+}, video views {growth['latest_video_views']:+}, likes {growth['latest_video_likes']:+}")
        else:
            print("  (first snapshot for this creator, run again later to see growth)")
        print()
        append_snapshot(current)   
    print(f"Snapshot saved to {SNAPSHOT_FILE}")   
if __name__ == "__main__":
    main()