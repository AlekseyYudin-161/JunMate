"""Экран входа — загрузка PDF или текстовое описание."""

import streamlit as st
from agents.parser import parse_resume
from agents.track import classify_track
from core.pdf_in import extract_text
from core.state import set_profile
from core.schemas import Profile


def render_upload_screen() -> None:
    """Рендерит экран входа с двумя путями."""
    st.header("🚀 JunMate")
    st.subheader("Подготовка резюме под hh.ru")
    st.write("Загрузите резюме в PDF или опишите свой опыт текстом.")

    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            pdf_file = st.file_uploader("Загрузить PDF", type=["pdf"])
        with col2:
            text_input = st.text_area(
                "Или опишите себя", 
                placeholder="Например: Иван, Python-джун, учился в МГТУ...",
                height=150
            )
        submitted = st.form_submit_button("Начать анализ", type="primary")

    if submitted:
        if pdf_file:
            _process_pdf(pdf_file)
        elif text_input.strip():
            _process_text(text_input.strip())
        else:
            st.error("Пожалуйста, загрузите PDF или введите текст.")


def _process_pdf(pdf_file) -> None:
    """Обрабатывает загруженный PDF."""
    progress_bar = st.progress(0, text="Извлечение текста...")

    try:
        pdf_bytes = pdf_file.read()
        text = extract_text(pdf_bytes)
        progress_bar.progress(33, text="Парсинг резюме...")
        _analyze_and_store(text, progress_bar)
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Ошибка обработки PDF: {e}")


def _process_text(text: str) -> None:
    """Обрабатывает текстовое описание."""
    progress_bar = st.progress(0, text="Парсинг описания...")
    _analyze_and_store(text, progress_bar)


def _analyze_and_store(text: str, progress_bar) -> None:
    """Парсит текст через A1 и сохраняет Profile."""
    try:
        # A1: Parser
        profile: Profile = parse_resume(text)
        set_profile(profile)
        progress_bar.progress(50, text="Классификация трека...")

        # A2: Track
        track_result = classify_track(profile)
        st.session_state.track = track_result.model_dump()
        progress_bar.progress(100, text="Готово!")

        st.success("Анализ завершён!")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Извлечённый профиль:**")
            st.json(profile.model_dump())
        with col2:
            st.write("**Определённый трек:**")
            st.json(track_result.model_dump())

        if st.button("Продолжить к диалогу"):
            st.session_state.screen = "chat"
            st.rerun()
    except Exception as e:
        st.error(f"Ошибка парсинга: {e}")
