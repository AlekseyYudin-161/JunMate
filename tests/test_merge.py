"""Тесты для детерминированного слияния профиля. 
Проверка, что merge_profile не теряет данные при слиянии. Страховка от регрессий
"""

from core.merge import merge_profile

def test_add_skill_no_overwrite():
    profile = {"skills": ["Python"]}
    patch = {"skills": ["Docker"]}
    result = merge_profile(profile, patch)
    assert "Python" in result["skills"]
    assert "Docker" in result["skills"]

def test_update_project_keeps_bullets():
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
    profile = {"contacts": {"email": "a@b.ru", "phone": "123"}}
    patch = {"contacts": {"email": "a@b.ru", "phone": "123", "github": "url"}}
    result = merge_profile(profile, patch)
    assert result["contacts"]["email"] == "a@b.ru"
    assert result["contacts"]["github"] == "url"

def test_empty_patch():
    profile = {"full_name": "Ivan"}
    result = merge_profile(profile, {})
    assert result == profile
