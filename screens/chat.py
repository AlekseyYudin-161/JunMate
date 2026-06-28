"""Экран чата — диалог с turn-агентом."""

import re
from datetime import datetime
import streamlit as st
from agents.turn import get_next_turn
from agents.rewriter import rewrite_resume
from agents.critic import critique_resume
from core.merge import merge_profile
from core.pdf_out import generate_pdf
from core.state import get_profile, set_profile
from core.schemas import SkillMatch
from core.schemas import Profile

MAX_QUESTIONS = 6                   # лимит вопросов в первом (основном) проходе диалога
REFINE_QUESTIONS = 3                # лимит вопросов в режиме добора после «Доделать»


def _safe_filename(profile) -> str:
    """
    Создает корректное имя PDF: 
    ФИО_роль_CV_дата.pdf, без недопустимых в имени файла символов.
    """
    name = profile.full_name or "resume"
    role = profile.target_role or "CV"
    date = datetime.now().strftime("%d-%m-%Y")
    raw = f"{name}_{role}_CV_{date}.pdf"
    raw = re.sub(r'[/\\:*?"<>|]', "", raw)
    return raw.replace(" ", "_")


@st.dialog("Сбросить диалог")
def reset_dialog():
    st.write("Сбросить диалог? Улучшение вашего резюме сбросится и диалог начнётся заново. Это действие необратимо.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Отмена", type="secondary", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Сбросить", type="primary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


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
        st.session_state.refine_mode = False                        # стартуем в основном режиме (лимит 6)
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

                # Раунд 1: A5
                resume_output = rewrite_resume(
                    profile=profile,
                    track=track,
                    gap=gap,
                    history=st.session_state.messages
                )

                # Раунд 2: A6 (Critic)
                with st.spinner("Проверяем на соответствие фактам..."):
                    critique = critique_resume(
                        profile=profile,
                        history=st.session_state.messages,
                        content_markdown=resume_output.content_markdown
                    )
                    st.session_state.critique = critique.model_dump()

                # Раунд 3: Повторный A5, если есть галлюцинации
                if not critique.grounding_ok:
                    with st.spinner("Исправляем замечания критика..."):
                        resume_output = rewrite_resume(
                            profile=profile,
                            track=track,
                            gap=gap,
                            history=st.session_state.messages,
                            fixes=critique.fixes
                        )

                st.session_state.resume_output = resume_output.model_dump()

        res = st.session_state.resume_output
        crit = st.session_state.get("critique")

        st.markdown(res["content_markdown"])

        # Отображение замечаний критика
        if crit and not crit.get("grounding_ok"):
            with st.expander("🔍 Замечания критика (были учтены при перегенерации)", expanded=False):
                if crit.get("fabricated_claims"):
                    st.error("**Найдены неподтвержденные факты:**")
                    for claim in crit["fabricated_claims"]:
                        st.write(f"• {claim}")
                if crit.get("fixes"):
                    st.warning("**Рекомендованные исправления:**")
                    for fix in crit["fixes"]:
                        st.write(f"• {fix}")

        if res.get("warnings"):
            with st.expander("⚠️ Рекомендации по улучшению"):
                for w in res["warnings"]:
                    st.write(f"• {w}")
        col1, col2 = st.columns(2)

        with col1:
            pdf_bytes = generate_pdf(res["content_markdown"])
            st.download_button(
                label="📥 Хорошо, Скачать PDF",
                data=pdf_bytes,
                file_name=_safe_filename(profile),
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        with col2:
            if st.button("✏️ Доделать", use_container_width=True):
                st.session_state.show_preview = False
                st.session_state.ready_to_render = False
                st.session_state.refine_mode = True                 # ВКЛючить режим добора (лимит REFINE_QUESTIONS=3)
                # Сбрасываем счетчик раунда
                st.session_state.start_msg_idx = len(st.session_state.messages)
                # Очищаем кэш рерайта и критика
                if "resume_output" in st.session_state:
                    del st.session_state.resume_output
                if "critique" in st.session_state:
                    del st.session_state.critique

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
        # Кнопки управления над чатом
        c1, _, c3 = st.columns([1, 4, 2])
        with c1:
            with st.popover("➕"):
                st.link_button("🐞 Сообщить о баге", "https://forms.gle/R4FPFTnoy6sjt7Mj7", use_container_width=True)
                st.link_button("💬 Обратная связь", "https://forms.gle/7oikcFZEs5QupgJC9", use_container_width=True)

        with c3:
            if st.button("🗑️ Сбросить диалог", type="primary", use_container_width=True):
                reset_dialog()

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
