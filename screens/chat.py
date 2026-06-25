"""Экран чата — диалог с turn-агентом."""

import streamlit as st

from agents.turn import get_next_turn
from core.merge import merge_profile
from core.state import get_profile, set_profile
from core.schemas import Profile

MAX_QUESTIONS = 6

def render_chat_screen() -> None:
    """Рендерит экран диалога."""
    st.header("💬 Диалог с JunMate")
    
    profile = get_profile()
    track_data = st.session_state.get("track", {})
    track = track_data.get("track", "Industry")
    target_role = profile.target_role or "Junior Developer"
    
    # Инициализация первого сообщения, если пусто
    if not st.session_state.messages:
        gap_data = st.session_state.get("gap", {})
        missing = gap_data.get("missing", []) if gap_data else []
        
        if not profile.target_role:
            initial_msg = "Привет! Я помогу тебе подготовить резюме. Какую именно IT-роль ты сейчас рассматриваешь (например, Python Developer, Data Analyst)?"
        elif missing:
            initial_msg = f"Привет! Помогу усилить резюме на позицию {target_role}. Я вижу, что в профиле не указаны: {', '.join(missing[:2])}. Расскажи подробнее про свой опыт с этими технологиями."
        else:
            initial_msg = f"Привет! Помогу усилить резюме на позицию {target_role}. Расскажи про свой главный проект: какую задачу решал и какой результат получил?"
            
        st.session_state.messages.append({"role": "assistant", "content": initial_msg})

    # Отображение истории
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Проверка готовности к рендеру
    ready_to_render = st.session_state.get("ready_to_render", False)

    if ready_to_render:
        st.success("Профиль достаточно заполнен!")
        if st.button("Показать резюме", type="primary"):
            st.info("Рендер будет реализован в следующей задаче.")

    # Поле ввода
    if not ready_to_render:
        if prompt := st.chat_input("Ваш ответ..."):
            # 1. Сохраняем сообщение пользователя
            st.session_state.messages.append({"role": "user", "content": prompt})

            # 2. Вызываем агента
            with st.spinner("JunMate думает..."):
                turn_result = get_next_turn(
                    profile=profile,
                    history=st.session_state.messages[:-1],
                    track=track,
                    target_role=target_role,
                    user_message=prompt
                )

            # 3. Применяем патч
            if turn_result.profile_patch:
                new_profile_dict = merge_profile(profile.model_dump(), turn_result.profile_patch)
                set_profile(Profile.model_validate(new_profile_dict))

            # 4. Сохраняем ответ помощника
            st.session_state.messages.append({"role": "assistant", "content": turn_result.reply})

            # 5. Проверяем лимиты
            user_msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
            if turn_result.ready_to_render or user_msg_count >= MAX_QUESTIONS:
                st.session_state.ready_to_render = True

            st.rerun()

    # Сайдбар с текущим Profile для проверки merge
    with st.sidebar:
        st.subheader("Текущий Profile (Debug)")
        st.json(get_profile().model_dump())
