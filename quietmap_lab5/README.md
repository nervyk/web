# quietmap (ЛР5-ЛР8 Django)

Тема: **Карта тихих мест**.

## Запуск
```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Проверка маршрутов
- `/` — главная страница с данными из БД
- `/spots/kovorking-na-krasnom/` — детальная страница по slug
- `/areas/center/?noise=high&tag=noise-high&sort=new` — фильтрация и сортировка в вебе
- `/categories/center/` — выборка по категории (ForeignKey)
- `/tags/` и `/tags/reading/` — теги и страницы тегов (ManyToMany)
- `/archive/2024/` — архив с кастомным year-конвертером
- `/archive404/2099/` — генерация Http404

## Демонстрационные команды
- `python manage.py demo_spot_crud` — CRUD (ЛР7)
- `python manage.py demo_lab8_queries` — Q/F/Value, annotate, aggregate, группировка, DB functions (ЛР8)

## ЛР9: админ-панель
- `/admin/` — админ-панель Django
- учебный суперпользователь: `root`
- учебный пароль: `1234`
- в админке настроены список мест, поиск, фильтры, пользовательские поля, действия и внешний вид

## Кастомный 404
В `quietmap/settings.py` временно:
- `DEBUG = False`
- `ALLOWED_HOSTS = ['127.0.0.1', 'localhost']`
