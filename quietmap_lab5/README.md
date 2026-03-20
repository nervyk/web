# quietmap_lab5 (ЛР5 Django)

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
- `/` — главная
- `/spots/3/` — динамический int
- `/areas/centr/?time=morning&noise=low` — slug + GET (GET печатается в консоль)
- `/archive/2020/` — собственный конвертер year4 (4 цифры)
- `/archive/2026/` — redirect на главную по имени маршрута `home`
- `/archive404/2026/` — генерация Http404 (работает с handler404 при DEBUG=False)

## Кастомный 404
В `quietmap/settings.py` временно:
- `DEBUG = False`
- `ALLOWED_HOSTS = ['127.0.0.1', 'localhost']`
