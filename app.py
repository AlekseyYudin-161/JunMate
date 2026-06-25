"""Точка входа JunMate — роутинг на страницы."""

import logging
import streamlit as st
from core.state import init_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    st.set_page_config(page_title="JunMate", page_icon="🚀", layout="centered")
    init_state()

    # закомментировать на проде
    if st.sidebar.button("Сбросить всё"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    # ----------------------------------------------
    screen = st.session_state.get("screen", "welcome")

    if screen == "welcome":
        from screens.welcome import render_upload_screen
        render_upload_screen()
    elif screen == "chat":
        from screens.chat import render_chat_screen
        render_chat_screen()


if __name__ == "__main__":
    main()
