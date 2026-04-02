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

        if views < 10:
            continue

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
            or ""
        )

        video_id = item.get("id")

        videos.append({
            "video_id": video_id,
            "title": snippet.get("title", "Untitled"),
            "channel": snippet.get("channelTitle", "Unknown Channel"),
            "published": snippet.get("publishedAt", "")[:10],
            "views": views,
            "thumbnail": thumbnail_url,
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })

    videos.sort(key=lambda x: x["published"], reverse=True)
    return videos


@app.route("/")
def index():
    error = None
    videos = []
    featured_video_id = None

    try:
        if not API_KEY:
            raise Exception("Server API key is missing.")

        ids = get_recent_video_ids()
        videos = get_video_details(ids)

        if videos:
            featured_video_id = videos[0]["video_id"]

    except requests.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "unknown"

        if status_code == 403:
            error = "YouTube API access is currently unavailable. Please try again later."
        else:
            error = f"API request failed with status {status_code}."

        print("HTTP error from YouTube API:", e)

    except Exception as e:
        error = "Something went wrong while loading videos."
        print("General app error:", e)

    return render_template(
        "index.html",
        videos=videos,
        error=error,
        featured_video_id=featured_video_id
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)