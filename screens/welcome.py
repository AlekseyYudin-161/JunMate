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

    # Версия ключей виджетов — инкремент сбрасывает file_uploader/text_area (см. «Очистить/Загрузить другое резюме»)
    if "upload_version" not in st.session_state:
        st.session_state.upload_version = 0
    ver = st.session_state.upload_version

    col1, col2 = st.columns(2)
    with col1:
        # key с версией: смена версии = новый чистый виджет
        pdf_file = st.file_uploader("Загрузить PDF", type=["pdf"], key=f"pdf_upload_{ver}")
    with col2:
        text_input = st.text_area(
            "Или опишите себя", 
            placeholder="Например: Иван, Python-джун, учился в МГТУ...",
            height=150,
            key=f"text_input_{ver}"                       # key с версией для сброса
        )

    # Кнопки разведены по краям (распорка посередине), чтобы юзер не промахнулся
    btn_col1, _, btn_col2 = st.columns([2, 2, 3])
    with btn_col1:
        start_clicked = st.button("Начать анализ", type="primary", use_container_width=True)
    with btn_col2:
        clear_clicked = st.button(
            "Очистить / Загрузить другое резюме",          # понятнее, чем просто «Очистить»
            type="secondary", use_container_width=True
        )

    # Очистка: сброс результатов анализа + смена версии ключей (очищает загрузку/текст)
    if clear_clicked:
        for k in ("profile", "track", "gap"):
            st.session_state.pop(k, None)                 # убрать результаты анализа, если есть
        st.session_state.upload_version += 1              # новый ключ → пустые file_uploader/text_area
        st.rerun()

    if start_clicked:
        if pdf_file:
            _process_pdf(pdf_file)
        elif text_input.strip():
            _process_text(text_input.strip())
        else:
            st.error("Пожалуйста, загрузите PDF или введите текст.")

    if st.session_state.get("profile"):
        st.subheader("Результаты анализа")

        # 1. Трек
        track_data = st.session_state.get("track")
        if track_data:
            st.info(f"**Ваш карьерный трек:** {track_data.get('track')}")

        # 2. Роль и Gap
        gap_data = st.session_state.get("gap")
        profile = st.session_state.get("profile")
        target_role = profile.get("target_role") if profile else None

        if target_role:
            st.write(f"**Целевая роль:** {target_role}")
            if gap_data:
                if gap_data.get("have"):
                    st.write("**Что у вас уже есть:**", ", ".join(gap_data["have"]))
                if gap_data.get("missing"):
                    st.write("**Чего не хватает:**", ", ".join(gap_data["missing"]))
        else:
            st.warning("Целевая роль не определена. Уточним её в ходе диалога.")

        def set_chat_screen():
            st.session_state.screen = "chat"

        st.button("Перейти к диалогу →", type="primary", on_click=set_chat_screen)


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
        if target_role:
            gap_result = match_skills(profile, target_role)
            st.session_state.gap = gap_result.model_dump()
        else:
            st.session_state.gap = None

        progress_bar.empty()
    except Exception as e:
        st.error(f"Ошибка парсинга: {e}")
