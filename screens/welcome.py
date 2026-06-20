"""Экран входа — загрузка PDF или текстовое описание."""
import streamlit as st

from agents.matcher import match_skills
from agents.parser import parse_resume
from agents.track import classify_track
from core.pdf_in import extract_text
from core.state import get_profile, init_state, set_profile
from core.schemas import Profile


def render_upload_screen() -> None:
    """Рендерит экран входа с двумя путями."""
    st.header("Загрузка резюме")
    st.write("Загрузите резюме в формате PDF или опишите себя текстом.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("PDF-резюме")
        pdf_file = st.file_uploader(
            "Загрузите PDF",
            type=["pdf"],
            key="pdf_uploader",
        )

    with col2:
        st.subheader("Нет резюме?")
        text_input = st.text_area(
            "Опишите себя текстом",
            placeholder="Расскажите о своём опыте, навыках, образовании...",
            height=200,
            key="text_input",
        )

    if st.button("Анализировать", type="primary"):
        if pdf_file:
            _process_pdf(pdf_file)
        elif text_input.strip():
            _process_text(text_input.strip())
        else:
            st.error("Загрузите PDF или введите текст.")


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
    """Парсит текст, классифицирует трек, делает gap-анализ."""
    # A1: Parser
    profile: Profile = parse_resume(text)
    set_profile(profile)
    progress_bar.progress(50, text="Классификация трека...")

    # A2: Track
    track_result = classify_track(profile)
    st.session_state.track = track_result.model_dump()
    progress_bar.progress(75, text="Gap-анализ...")

    # A3: Matcher
    target_role = profile.target_role or "Junior Developer"
    gap_result = match_skills(profile, target_role)
    st.session_state.gap = gap_result.model_dump()
    progress_bar.progress(100, text="Готово!")

    # Переход к чату
    st.session_state.screen = "chat"
    st.rerun()
