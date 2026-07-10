"""Тесты детерминированного слияния профиля (core/merge.py).
Проверяют, что merge_profile не теряет данные — страховка от регрессий.
"""

from core.merge import merge_profile

def test_add_skill_no_overwrite():
    """Новый навык добавляется, не затирая прежние."""

    profile = {"skills": ["Python"]}
    patch = {"skills": ["Docker"]}
    result = merge_profile(profile, patch)
    assert "Python" in result["skills"]
    assert "Docker" in result["skills"]

def test_update_project_keeps_bullets():
    """Обновление проекта сохраняет полный список буллетов, не дублируя элемент."""

    profile = {
        "projects": [
            {"name": "App", "bullets": ["b1", "b2"]}
        ]
    }
    patch = {
        "projects": [
            {"name": "App", "bullets": ["b1", "b2", "b3"]}
        ]
    }
    result = merge_profile(profile, patch)
    assert len(result["projects"]) == 1
    assert len(result["projects"][0]["bullets"]) == 3

def test_contacts_preserved():
    """Добавление ссылки в contacts не затирает email и телефон."""

    profile = {"contacts": {"email": "a@b.ru", "phone": "123"}}
    patch = {"contacts": {"email": "a@b.ru", "phone": "123", "github": "url"}}
    result = merge_profile(profile, patch)
    assert result["contacts"]["email"] == "a@b.ru"
    assert result["contacts"]["github"] == "url"

def test_empty_patch():
    """Пустой патч не изменяет профиль."""

    profile = {"full_name": "Ivan"}
    result = merge_profile(profile, {})
    assert result == profile
