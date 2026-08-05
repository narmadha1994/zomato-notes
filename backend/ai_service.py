import json
import os
import re

from dotenv import load_dotenv

load_dotenv()


def get_ai_response(
    user_message: str,
    system_prompt: str
) -> str:
    """
    Returns an AI response.

    When MOCK_AI=1, this returns a deterministic fake JSON
    without calling any external API.

    The real API path can be added later.
    """

    mock_mode = os.getenv("MOCK_AI", "1") == "1"

    if mock_mode:

        # Remove punctuation
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", user_message.lower())

        words = cleaned.split()

        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "this",
            "that",
            "have",
            "from",
            "into",
            "your",
            "about",
            "there",
            "their",
            "been",
            "were",
            "will",
            "would",
            "should",
            "could",
            "very",
            "also",
            "then",
            "than",
            "after",
            "before",
            "while",
            "when",
            "where",
            "what",
            "which",
            "into",
            "onto",
            "over",
            "under",
            "today"
        }

        keywords = []

        for word in words:
            if word not in stop_words and word not in keywords:
                keywords.append(word)

            if len(keywords) == 3:
                break

        if not keywords:
            keywords = ["note"]

        summary_words = user_message.split()[:20]

        summary = " ".join(summary_words)

        response = {
            "tags": keywords,
            "summary": summary
        }

        return json.dumps(response)

    # -----------------------------
    # Real LLM path (optional)
    # -----------------------------

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Enable MOCK_AI=1 or configure an API key."
        )

    raise NotImplementedError(
        "Real LLM integration will be added later."
    )