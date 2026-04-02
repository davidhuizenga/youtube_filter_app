@app.route("/")
def index():
    error = None
    videos = []

    try:
        if not API_KEY:
            raise Exception("Server API key is missing.")

        ids = get_recent_video_ids()
        videos = get_video_details(ids)

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

    return render_template("index.html", videos=videos, error=error)