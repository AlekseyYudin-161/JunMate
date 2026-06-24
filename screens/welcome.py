"""Экран входа — загрузка PDF или текстовое описание."""

import streamlit as st
from agents.parser import parse_resume
from agents.track import classify_track
from agents.matcher import match_skills
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
        progress_bar.progress(33, text="Классификация трека...")

        # A2: Track
        track_result = classify_track(profile)
        st.session_state.track = track_result.model_dump()
        progress_bar.progress(66, text="Анализ соответствия роли...")

        # A3: Matcher
        target_role = profile.target_role
        gap_result = None
        if target_role:
            gap_result = match_skills(profile, target_role)
            st.session_state.gap = gap_result.model_dump()
        else:
            st.session_state.gap = None

        progress_bar.progress(100, text="Готово!")
        st.success("Анализ завершён!")

        # Первое сообщение (статичное)
        st.subheader("Результаты анализа")

        track_name = track_result.track
        st.info(f"**Ваш карьерный трек:** {track_name}")

        if gap_result:
            st.write(f"**Целевая роль:** {gap_result.target_role}")
            st.write("**Что у вас уже есть:**", ", ".join(gap_result.have))
            if gap_result.missing:
                st.write("**Чего не хватает:**", ", ".join(gap_result.missing))
        else:
            st.warning("Целевая роль не определена. Мы уточним её в ходе диалога.")

        if st.button("Начать диалог", type="primary"):
            st.session_state.screen = "chat"
            st.rerun()
    except Exception as e:
        st.error(f"Ошибка парсинга: {e}")
