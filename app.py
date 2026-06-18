"""Точка входа JunMate — роутинг на страницы."""
import streamlit as st


def main() -> None:
    st.set_page_config(page_title="JunMate", page_icon="🚀", layout="centered")
    st.title("JunMate")
    st.write("ok")


if __name__ == "__main__":
    main()
