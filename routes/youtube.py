from flask import Blueprint, request, jsonify

youtube_bp = Blueprint("youtube", __name__)

@youtube_bp.route("/fetch", methods=["POST"])
def fetch_comments():
    data = request.json
    video_url = data.get("url", "")

    # Placeholder: real YouTube API integration will go here
    comments = [
        "This video is awesome!",
        "I didn’t like the editing.",
        "Great explanation!"
    ]

    return jsonify({"video_url": video_url, "comments": comments})
