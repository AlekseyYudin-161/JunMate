"""Утилиты для работы с session_state."""
import streamlit as st

from core.schemas import Profile


def init_state() -> None:
    """Инициализирует session_state базовыми ключами."""
    if "profile" not in st.session_state:
        st.session_state.profile = Profile().model_dump()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "track" not in st.session_state:
        st.session_state.track = None
    if "gap" not in st.session_state:
        st.session_state.gap = None


def get_profile() -> Profile:
    """Возвращает текущий Profile из session_state."""
    return Profile.model_validate(st.session_state.get("profile", {}))


def set_profile(profile: Profile) -> None:
    """Записывает Profile в session_state."""
    st.session_state.profile = profile.model_dump()
