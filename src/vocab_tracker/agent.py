import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from vocab_tracker import repository as repo

load_dotenv()
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

SYSTEM_PROMPT = """You are a vocabulary coach inside a word-tracking app.

You can see the words this user has saved and how they have performed on reviews.
Always check with your tools before answering and never guess what words they know.
Be concise and encouraging. When quizzing, ask one word at a time and wait.
"""


def build_agent(user_id: int):
    """Build an agent whose tools are locked to one user."""

    @tool
    def list_words() -> list[dict]:
        """List every word this user has saved, with definitions."""
        return [
            {
                "word": w.word,
                "definition": w.definition,
                "translation": w.translation,
            }
            for w in repo.get_words(user_id)
        ]

    @tool
    def weakest_words(limit: int = 5) -> list[dict]:
        """The words this user gets wrong most often, with accuracy and review counts."""
        rows = repo.get_word_stats(user_id, limit=limit)
        for row in rows:
            if row.get("last_reviewed"):
                row["last_reviewed"] = row["last_reviewed"].isoformat()
        return rows

    @tool
    def save_word(
        word: str,
        definition: str,
        translation: str = "",
        example: str = "",
    ) -> str:
        """Save a new word to this user's vocabulary list."""
        repo.add_word(
            user_id,
            word.strip().lower(),
            definition=definition,
            translation=translation or None,
            example=example or None,
        )
        return f"Saved “{word}”."

    llm = ChatOpenAI(model=MODEL, temperature=0)
    return create_agent(
        llm,
        tools=[list_words, weakest_words, save_word],
        system_prompt=SYSTEM_PROMPT,
    )