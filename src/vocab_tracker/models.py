from datetime import datetime

from pydantic import BaseModel


class Word(BaseModel):
    id: int
    user_id: int
    word: str
    language: str
    definition: str | None = None
    translation: str | None = None
    example: str | None = None
    created_at: datetime


class Review(BaseModel):
    id: int
    word_id: int
    correct: bool
    reviewed_at: datetime