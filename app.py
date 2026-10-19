import streamlit as st
from psycopg.errors import UniqueViolation
from vocab_tracker import llm
from vocab_tracker import auth
import pandas as pd
from vocab_tracker import repository as repo
from vocab_tracker.agent import build_agent

st.set_page_config(page_title="Vocab Tracker", page_icon="📚", layout="wide")

if "user_id" not in st.session_state:
    st.session_state.user_id = None


def login_page():
    st.title("Vocab Tracker")
    tab_login, tab_register = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log in"):
                user_id = auth.login(email, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.rerun()
                else:
                    st.error("Wrong email or password.")

    with tab_register:
        with st.form("register_form"):
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            if st.form_submit_button("Create account"):
                try:
                    st.session_state.user_id = auth.register(email, password)
                    st.rerun()
                except UniqueViolation:
                    st.error("That email is already registered.")

def add_word_page(user_id: int):
    st.subheader("Add a word")

    for field in ("definition", "translation", "example"):
        st.session_state.setdefault(field, "")
    if flash := st.session_state.pop("_flash", None):
        st.success(flash)
    if st.session_state.pop("_clear_fields", False):
        for field in ("definition", "translation", "example", "new_word"):
            st.session_state[field] = ""
    col_word, col_lang, col_btn = st.columns([3, 1, 1])
    word = col_word.text_input("Word", key="new_word")
    language = col_lang.selectbox("Language", ["en", "fr", "es", "de", "ar"])
    col_btn.markdown("<br>", unsafe_allow_html=True)

    if col_btn.button("Generate", use_container_width=True):
        if not word.strip():
            st.error("Type a word first.")
        else:
            with st.spinner("Generating…"):
                details = llm.generate_word_details(word.strip(), language)
            st.session_state.definition = details.definition
            st.session_state.translation = details.translation
            st.session_state.example = details.example
            st.rerun()

    st.text_area("Definition", key="definition")
    st.text_input("Translation", key="translation")
    st.text_input("Example sentence", key="example")

    if st.button("Save", type="primary"):
        if not word.strip():
            st.error("A word is required.")
        else:
            repo.add_word(
                user_id,
                word.strip(),
                language=language,
                definition=st.session_state.definition or None,
                translation=st.session_state.translation or None,
                example=st.session_state.example or None,
            )
            st.session_state["_flash"] = f"Saved “{word.strip()}”."
            st.session_state["_clear_fields"] = True
            st.rerun()

def my_words_page(user_id: int):
    st.subheader("My words")
    words = repo.get_words(user_id)
    if not words:
        st.info("No words yet,add one on the first tab.")
        return

    df = pd.DataFrame([w.model_dump() for w in words])
    search = st.text_input("Filter", placeholder="type to filter…")
    if search:
        df = df[df["word"].str.contains(search, case=False, regex=False)]

    st.dataframe(
        df[["word", "language", "definition", "translation", "example", "created_at"]],
        use_container_width=True,
        hide_index=True,
    )


def dashboard_page(user_id: int):
    st.subheader("Dashboard")
    stats = repo.get_word_stats(user_id)
    if not stats:
        st.info("No words yet.")
        return

    df = pd.DataFrame(stats)
    total_words = len(df)
    reviewed = int((df["times_reviewed"] > 0).sum())
    total_reviews = int(df["times_reviewed"].sum())
    overall = df["times_correct"].sum() / total_reviews if total_reviews else None

    c1, c2, c3 = st.columns(3)
    c1.metric("Words", total_words)
    c2.metric("Reviewed", f"{reviewed}/{total_words}")
    c3.metric("Accuracy", f"{overall:.0%}" if overall is not None else "—")

    st.markdown("**Weakest words**")
    weak = df[df["times_reviewed"] > 0].head(10)
    if weak.empty:
        st.caption("Nothing reviewed yet, the quiz will fill this in.")
    else:
        st.bar_chart(weak.set_index("word")["accuracy"], height=260)

def quiz_page(user_id: int):
    st.subheader("Quiz")

    if "quiz_word" not in st.session_state:
        st.session_state.quiz_word = repo.get_quiz_word(user_id)
        st.session_state.quiz_result = None

    card = st.session_state.quiz_word
    if not card:
        st.info("Add some words first.")
        return

    st.markdown(f"### {card['definition'] or '(no definition saved)'}")
    if card["translation"]:
        st.caption(f"🇫🇷 {card['translation']}")

    if st.session_state.quiz_result is None:
        with st.form("quiz_form", clear_on_submit=True):
            answer = st.text_input("Which word is this?")
            if st.form_submit_button("Check"):
                correct = answer.strip().lower() == card["word"].strip().lower()
                repo.record_review(card["id"], correct)
                st.session_state.quiz_result = correct
                st.rerun()
    else:
        if st.session_state.quiz_result:
            st.success(f"Correct — **{card['word']}**")
        else:
            st.error(f"The word was **{card['word']}**")
        if card["example"]:
            st.caption(card["example"])
        if st.button("Next word", type="primary"):
            st.session_state.quiz_word = repo.get_quiz_word(user_id)
            st.session_state.quiz_result = None
            st.rerun()
def chat_page(user_id: int):
    st.subheader("Coach")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    if st.session_state.chat and st.button("Clear conversation"):
        st.session_state.chat = []
        st.rerun()

    for msg in st.session_state.chat:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ask about your words…"):
        st.session_state.chat.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                agent = build_agent(user_id)
                result = agent.invoke({"messages": st.session_state.chat})
                reply = result["messages"][-1].content
            st.write(reply)

        st.session_state.chat.append({"role": "assistant", "content": reply})
def main_app():
    user_id = st.session_state.user_id

    with st.sidebar:
        st.caption(f"User #{user_id}")
        if st.button("Log out"):
            st.session_state.user_id = None
            st.rerun()

    st.title("Vocab Tracker")
    tab_add, tab_words,tab_quiz, tab_dash,tab_chat  = st.tabs(["Add", "My words","Quiz", "Dashboard","Coach"])

    with tab_add:
        add_word_page(user_id)
    with tab_words:
        my_words_page(user_id)
    with tab_dash:
        dashboard_page(user_id)
    with tab_quiz:
        quiz_page(user_id)
    with tab_chat:
        chat_page(user_id)
if st.session_state.user_id is None:
    login_page()
else:
    main_app()