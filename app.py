import streamlit as st
from psycopg.errors import UniqueViolation

from vocab_tracker import auth

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


def main_app():
    with st.sidebar:
        st.caption(f"User #{st.session_state.user_id}")
        if st.button("Log out"):
            st.session_state.user_id = None
            st.rerun()

    st.title("Vocab Tracker")
    st.info("Logged in. Pages come next.")


if st.session_state.user_id is None:
    login_page()
else:
    main_app()