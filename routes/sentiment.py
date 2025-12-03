from flask import Blueprint, request, jsonify
from services.sentiment_service import analyze_sentiment

sentiment_bp = Blueprint("sentiment", __name__)

@sentiment_bp.route("/sentiment", methods=["POST"])
def sentiment_analysis():
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"]
    result = analyze_sentiment(text)
    return jsonify(result)
