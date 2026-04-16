from django.contrib import admin
from django.urls import include, path

from spots.views import page_not_found

admin.site.site_header = "Панель администрирования карты тихих мест"
admin.site.site_title = "Админ-панель QuietMap"
admin.site.index_title = "Управление местами, категориями и тегами"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("spots.urls")),
]

handler404 = page_not_found
