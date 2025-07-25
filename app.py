"""
Flask application to serve a devotional Q&A website powered by
Srila Prabhupada's commentaries.  The app loads a small dataset
containing translations and purports from "Bhagavad‑gita As It Is"
and uses a simple keyword matching approach to return passages
relevant to a visitor's question.  Answers always cite the book,
chapter and verse and end with the prescribed benediction.

To run locally:

    pip install -r requirements.txt
    python app.py

The web server will be available at http://127.0.0.1:5000/
"""

import json
import re
from pathlib import Path

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Load the devotional data once at startup.  The JSON file
# contains a list of records with fields: book, chapter, verse,
# translation, purport and author.  If this file grows large or
# multiple books are added, consider storing the data in a more
# efficient search index or database.
DATA_PATH = Path(__file__).resolve().parent / "data.json"
try:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        DATA = json.load(f)
except FileNotFoundError:
    DATA = []


def search_passage(query: str):
    """Return the record most relevant to the given query.

    This implementation performs a simple keyword match across
    each record's translation and purport.  It counts how many
    of the query words appear in the passage and returns the
    passage with the highest score.  A more advanced approach
    could use vector embeddings or full‑text search, but this
    lightweight method requires no external services.

    Args:
        query: The user's question or keywords.

    Returns:
        A dict representing the best matching record, or None if
        nothing was found.
    """
    # Normalize query into lowercase words
    words = re.findall(r"\w+", query.lower())
    if not words:
        return None
    best_record = None
    best_score = 0
    for rec in DATA:
        text = f"{rec.get('translation', '')} {rec.get('purport', '')}".lower()
        score = sum(text.count(word) for word in words)
        if score > best_score:
            best_score = score
            best_record = rec
    return best_record


@app.route("/")
def index():
    """Serve the main page containing the question form."""
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    """Receive an AJAX request containing the user's question and
    respond with a passage from Srila Prabhupada's works.

    The response always includes a citation (book, chapter, verse)
    and ends with the blessing as requested by the user.  If no
    relevant passage is found, an apologetic message is returned.
    """
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    record = search_passage(question)
    if record:
        answer = (
            f"{record['translation']}\n\n"
            f"{record['purport']}\n\n"
            f"({record['book']}, Chapter {record['chapter']}, Verse {record['verse']}) "
            f"– {record['author']}. "
            f"Chant Hare Krishna and be happy."
        )
    else:
        answer = "This information is not available in the provided texts. Chant Hare Krishna and be happy."
    return jsonify({"answer": answer})


if __name__ == "__main__":
    # Enable debug mode for development.  In production the
    # server should run behind a proper WSGI server such as
    # Gunicorn or uWSGI and debug should be disabled.
    app.run(debug=True)
