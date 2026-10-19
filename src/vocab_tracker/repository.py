from vocab_tracker.db import get_connection
from vocab_tracker.models import Word


# ---------- users ----------

def create_user(email: str, password_hash: str) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
            (email, password_hash),
        ).fetchone()
    return row["id"]


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (email,),
        ).fetchone()


# ---------- words ----------

def add_word(
    user_id: int,
    word: str,
    language: str = "en",
    definition: str | None = None,
    translation: str | None = None,
    example: str | None = None,
) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO words (user_id, word, language, definition, translation, example)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, word, language) DO UPDATE
                SET definition  = EXCLUDED.definition,
                    translation = EXCLUDED.translation,
                    example     = EXCLUDED.example
            RETURNING id
            """,
            (user_id, word, language, definition, translation, example),
        ).fetchone()
    return row["id"]


def get_words(user_id: int) -> list[Word]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM words WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [Word(**row) for row in rows]


# ---------- reviews ----------

def record_review(word_id: int, correct: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO reviews (word_id, correct) VALUES (%s, %s)",
            (word_id, correct),
        )
def get_quiz_word(user_id: int) -> dict | None:
    """Pick a word to review: sample randomly from the five weakest."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM (
                SELECT w.id, w.word, w.definition, w.translation, w.example,
                       COALESCE(
                           COUNT(r.id) FILTER (WHERE r.correct)::float
                           / NULLIF(COUNT(r.id), 0), -1
                       ) AS accuracy,
                       MAX(r.reviewed_at) AS last_reviewed
                FROM words w
                LEFT JOIN reviews r ON r.word_id = w.id
                WHERE w.user_id = %s
                GROUP BY w.id
                ORDER BY accuracy, last_reviewed NULLS FIRST
                LIMIT 5
            ) weakest
            ORDER BY random()
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()