"""Экран чата — диалог с turn-агентом."""

import streamlit as st
from agents.turn import get_next_turn
from agents.rewriter import rewrite_resume
from core.merge import merge_profile
from core.state import get_profile, set_profile
from core.schemas import SkillMatch
from core.schemas import Profile

MAX_QUESTIONS = 6                   # лимит вопросов в первом (основном) проходе диалога
REFINE_QUESTIONS = 3                # лимит вопросов в режиме добора после «Доделать»


def render_chat_screen() -> None:
    """Рендерит экран диалога."""
    st.header("💬 Диалог с JunMate")

    profile = get_profile()
    track_data = st.session_state.get("track", {})
    track = track_data.get("track", "Industry")
    target_role = profile.target_role or "Junior Developer"

    # Инициализация первого сообщения, если пусто
    if not st.session_state.messages:
        st.session_state.start_msg_idx = 0
        st.session_state.refine_mode = False        # стартуем в основном режиме (лимит 6)
        gap_data = st.session_state.get("gap", {})
        missing = gap_data.get("missing", []) if gap_data else []

        if not profile.target_role:
            initial_msg = "Привет! Я помогу тебе подготовить резюме. Какую именно IT-роль ты сейчас рассматриваешь (например, Python Developer, Data Analyst)?"
        elif missing:
            initial_msg = f"Привет! Помогу усилить резюме на позицию {target_role}. Я вижу, что в профиле не указаны: {', '.join(missing[:2])}. Расскажи подробнее про свой опыт с этими технологиями."
        else:
            initial_msg = f"Привет! Помогу усилить резюме на позицию {target_role}. Расскажи про свой главный проект: какую задачу решал(-а) и какой результат получил(-а)?"

        st.session_state.messages.append({"role": "assistant", "content": initial_msg})

    # Отображение истории
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Проверка готовности к рендеру
    ready_to_render = st.session_state.get("ready_to_render", False)

    if ready_to_render:
        st.success("Профиль достаточно заполнен!")
        if st.button("Показать резюме", type="primary", key="show_resume_btn"):
            st.session_state.show_preview = True

    # Превью резюме
    if st.session_state.get("show_preview"):
        st.divider()
        st.subheader("📄 Предпросмотр резюме (hh.ru)")

        # Вызываем рерайтер, если результата еще нет
        if "resume_output" not in st.session_state:
            with st.spinner("Формируем резюме..."):
                gap_data = st.session_state.get("gap")
                gap = SkillMatch.model_validate(gap_data) if gap_data else None

                resume_output = rewrite_resume(
                    profile=profile,
                    track=track,
                    gap=gap,
                    history=st.session_state.messages
                )
                st.session_state.resume_output = resume_output.model_dump()

        res = st.session_state.resume_output
        st.markdown(res["content_markdown"])

        if res.get("warnings"):
            with st.expander("⚠️ Рекомендации по улучшению"):
                for w in res["warnings"]:
                    st.write(f"• {w}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Хорошо", type="primary", use_container_width=True):
                st.success("Отлично! В следующей задаче мы добавим скачивание PDF.")
        with col2:
            if st.button("✏️ Доделать", use_container_width=True):
                st.session_state.show_preview = False
                st.session_state.ready_to_render = False
                # Сбрасываем счетчик раунда
                st.session_state.start_msg_idx = len(st.session_state.messages)
                st.session_state.refine_mode = True                             # включаем режим добора (лимит REFINE_QUESTIONS=3)

                # Очищаем кэш рерайта
                if "resume_output" in st.session_state:
                    del st.session_state.resume_output

                # Генерируем новый вопрос от бота сразу, чтобы не ждать ввода пользователя
                with st.spinner("JunMate ищет, что еще уточнить..."):
                    turn_result = get_next_turn(
                        profile=profile,
                        history=st.session_state.messages,
                        track=track,
                        target_role=target_role,
                        user_message="Продолжим интервью. Задай еще один уточняющий вопрос."
                    )
                    st.session_state.messages.append({"role": "assistant", "content": turn_result.reply})
                st.rerun()

    # Поле ввода
    if not ready_to_render:
        if prompt := st.chat_input("Ваш ответ..."):
            # 1. Сохраняем сообщение пользователя
            st.session_state.messages.append({"role": "user", "content": prompt})

            if "start_msg_idx" not in st.session_state:
                st.session_state.start_msg_idx = 0

            current_round_msgs = st.session_state.messages[st.session_state.start_msg_idx:]
            current_user_msg_count = len([m for m in current_round_msgs if m["role"] == "user"])

            # Выбираем лимит в зависимости от режима: основной проход (6) или добор после «Доделать» (3)
            current_limit = REFINE_QUESTIONS if st.session_state.get("refine_mode") else MAX_QUESTIONS

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

            # 4. Формируем ответ помощника
            if current_user_msg_count >= current_limit:         # было MAX_QUESTIONS
                reply = "JunMate собрал достаточно информации. Можно посмотреть предварительное резюме."
                st.session_state.ready_to_render = True
            else:
                reply = turn_result.reply
                if turn_result.ready_to_render:
                    st.session_state.ready_to_render = True

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    # Сайдбар с текущим Profile для проверки merge
    with st.sidebar:
        st.subheader("Текущий Profile (Debug)")
        st.json(get_profile().model_dump())
