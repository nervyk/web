from django.urls import path, register_converter

from . import converters, views

register_converter(converters.FourDigitYearConverter, "year4")

urlpatterns = [
    path("", views.index, name="home"),
    path("about/", views.about, name="about"),
    path("spots/<slug:spot_slug>/", views.spot_detail, name="spot_detail"),
    path("areas/<slug:area_slug>/", views.area, name="area"),
    path("archive/<year4:year>/", views.archive, name="archive"),
    path("archive404/<year4:year>/", views.archive_404, name="archive404"),
]
