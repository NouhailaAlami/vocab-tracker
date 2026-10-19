import streamlit as st
from psycopg.errors import UniqueViolation
from vocab_tracker import llm
from vocab_tracker import auth
import pandas as pd
from vocab_tracker import repository as repo

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


def main_app():
    user_id = st.session_state.user_id

    with st.sidebar:
        st.caption(f"User #{user_id}")
        if st.button("Log out"):
            st.session_state.user_id = None
            st.rerun()

    st.title("Vocab Tracker")
    tab_add, tab_words, tab_dash = st.tabs(["Add", "My words", "Dashboard"])

    with tab_add:
        add_word_page(user_id)
    with tab_words:
        my_words_page(user_id)
    with tab_dash:
        dashboard_page(user_id)
if st.session_state.user_id is None:
    login_page()
else:
    main_app()