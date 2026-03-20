from datetime import datetime

MENU = [
    {"title": "Главная", "url_name": "home"},
    {"title": "О проекте", "url_name": "about"},
]


def build_base_context(title: str) -> dict:
    return {
        "title": title,
        "menu": MENU,
        "current_year": get_current_year(),
    }


def get_current_year() -> int:
    return datetime.now().year
