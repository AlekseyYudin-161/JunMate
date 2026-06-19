"""Точка входа JunMate — роутинг на страницы."""
import logging
import streamlit as st

logging.basicConfig(level=logging.INFO)


def main() -> None:
    st.set_page_config(page_title="JunMate", page_icon="🚀", layout="centered")
    st.title("JunMate")
    st.write("ok")


if __name__ == "__main__":
    main()
