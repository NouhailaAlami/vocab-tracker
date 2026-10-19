import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


class WordDetails(BaseModel):
    """Generated details for a vocabulary word."""

    definition: str = Field(description="One clear sentence, at most 20 words.")
    translation: str = Field(description="The French translation. One or two words.")
    example: str = Field(description="A natural sentence using the word.")


def generate_word_details(word: str, language: str = "en") -> WordDetails:
    llm = ChatOpenAI(model=MODEL, temperature=0)
    structured = llm.with_structured_output(WordDetails)
    return structured.invoke(
        f"The {language} word is '{word}'. "
        "Write a definition a language learner would understand — "
        "concise, concrete, no padding."
    )