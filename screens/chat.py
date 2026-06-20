"""Экран чата — диалог с turn-агентом."""
import streamlit as st

from core.state import get_profile, init_state


def render_chat_screen() -> None:
    """Рендерит экран диалога."""
    init_state()

    track = st.session_state.get("track")
    gap = st.session_state.get("gap")

    if track:
        st.header(f"Трек: {track['track']}")
        confidence = track.get("confidence", 0)
        st.write(f"Уверенность: {confidence:.0%}")
        if track.get("evidence"):
            st.write("**Обоснование:**")
            for ev in track["evidence"][:3]:
                st.write(f"• {ev}")

    if gap:
        st.write("**Пробелы в навыках:**")
        if gap.get("missing"):
            st.write(f"Не хватает: {', '.join(gap['missing'][:5])}")

    # История сообщений
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Поле ввода (заглушка для TASK 2)
    if prompt := st.chat_input("Ваш ответ..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
