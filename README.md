# Vocab Tracker

A vocabulary learning app with an AI coach that can read and write your word list.

## What it does

- **Add words:** type a word, an LLM generates the definition, French translation and an example sentence. Everything stays editable before saving.
- **Quiz:** shown a definition, type the word. Answers are recorded, weakest words are asked first.
- **Dashboard:** word count, review coverage, overall accuracy, and which words you keep getting wrong.
- **AI Coach:** a chat agent with tools over your own data. Ask *"which words am I weakest on?"*, *"quiz me"*, or *"add 'serendipity'"* and it queries or writes to the database accordingly.

## Stack

Python 3.12 · PostgreSQL 16 · Docker Compose · Streamlit · LangChain · OpenAI · psycopg 3 · Pydantic · bcrypt · uv

## Architecture
Three layers, each with one job:
1. **app.py**: Streamlit UI renders and holds session state.
                         ↓
**2. agent.py:** wraps repository functions as LLM tools.
**llm.py:** single-purpose structured generation.
                         ↓
**3. repository.py:** every SQL query in the project.
**db.py:** connection handling.


Two decisions worth calling out:

**The agent's tools are scoped to one user by closure, not by argument.** `build_agent(user_id)` defines its tools inside the function, so `user_id` is captured from the session and is invisible to the model.
The LLM decides *what* to do; the application decides *whose* data it touches. 

**Reviews are stored as individual rows, not counters.** A `times_wrong` column would be simpler but discards history. Keeping each review with its timestamp is what makes "which words have I been failing over the past month" answerable, and it's what the dashboard and the agent both read.

## Running the Project

Requires Docker and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/NouhailaAlami/vocab-tracker.git
cd vocab-tracker

cp .env.example .env
# add your OPENAI_API_KEY

docker compose up -d          # starts PostgreSQL, applies schema.sql
uv sync
uv run streamlit run app.py
```

Opens at `localhost:8501`.

## Project structure
```
vocab-tracker/
├── app.py                    # Streamlit entry point 
├── schema.sql                # table definitions, applied on first container boot
├── docker-compose.yml        # PostgreSQL service
├── pyproject.toml            # dependencies
├── uv.lock                   # pinned versions
├── .env.example
├── docs/
│   └── demo.gif
└── src/
    └── vocab_tracker/
        ├── __init__.py
        ├── db.py             # connection handling
        ├── models.py         # Pydantic models
        ├── repository.py     # every SQL query in the project
        ├── auth.py           # bcrypt hashing, login
        ├── llm.py            # structured word generation
        └── agent.py          # LangChain agent and its tools
```
## Roadmap

- Spaced repetition scheduling (SM-2) so reviews are due rather than random
- Word difficulty prediction trained on CEFR-levelled vocabulary lists
- Flashcard review mode
- Containerised app service so `docker compose up` starts everything

## Screenshots

### Add a word
<p align="center">
<img width="586" height="626" alt="image" src="https://github.com/user-attachments/assets/e497e8dc-3b6a-46d9-9d10-476d1046635d" />
</p>

The model proposes a definition, translation and example sentence. Everything stays editable before saving.
### AI Coach
<p align="center">
<img width="586" height="626" alt="image" src="https://github.com/user-attachments/assets/1535938a-dacd-4dfc-9431-54373cb8b979" />
</p>

The agent has tools over your own data : it can list your words, find the ones you keep missing, and save new ones.
