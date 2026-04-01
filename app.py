import os
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("YOUTUBE_API_KEY")

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def get_recent_video_ids():
    """
    Get recent videos matching the keyword.
    """
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat("T") + "Z"

    params = {
        "part": "snippet",
        "q": "hoe",
        "type": "video",
        "order": "date",
        "publishedAfter": seven_days_ago,
        "maxResults": 50,
        "key": API_KEY
    }

    response = requests.get(SEARCH_URL, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()

    video_ids = []
    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            video_ids.append(video_id)

    return video_ids


def get_video_details(video_ids):
    """
    Get full video data including stats.
    """
    if not video_ids:
        return []

    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }

    response = requests.get(VIDEOS_URL, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()
    videos = []

    for item in data.get("items", []):
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})

        views = int(stats.get("viewCount", 0))

        # 10+ views filter
        if views < 10:
            continue

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
            or ""
        )

        videos.append({
            "title": snippet.get("title", "Untitled"),
            "channel": snippet.get("channelTitle", "Unknown Channel"),
            "published": snippet.get("publishedAt", "")[:10],
            "views": views,
            "thumbnail": thumbnail_url,
            "url": f"https://www.youtube.com/watch?v={item.get('id')}"
        })

    # Newest first
    videos.sort(key=lambda x: x["published"], reverse=True)
    return videos


@app.route("/")
def index():
    error = None
    videos = []

    try:
        if not API_KEY:
            raise Exception("Missing API key in .env file")

        ids = get_recent_video_ids()
        videos = get_video_details(ids)

    except Exception as e:
        error = str(e)

    return render_template("index.html", videos=videos, error=error)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)