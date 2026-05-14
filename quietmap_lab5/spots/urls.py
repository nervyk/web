from django.urls import path, register_converter

from . import converters, views

register_converter(converters.FourDigitYearConverter, "year4")

urlpatterns = [
    path("", views.index, name="home"),
    path("about/", views.about, name="about"),
    path("forms/", views.forms_hub, name="forms_hub"),
    path("forms/manual/", views.plain_spot_add, name="plain_spot_add"),
    path("forms/model/", views.model_spot_add, name="model_spot_add"),
    path("forms/upload/", views.upload_file, name="upload_file"),
    path("spots/<slug:spot_slug>/", views.spot_detail, name="spot_detail"),
    path("categories/<slug:category_slug>/", views.category, name="category"),
    path("tags/", views.tags_index, name="tags_index"),
    path("tags/<slug:tag_slug>/", views.tag, name="tag"),
    path("areas/<slug:area_slug>/", views.area, name="area"),
    path("archive/<year4:year>/", views.archive, name="archive"),
    path("archive404/<year4:year>/", views.archive_404, name="archive404"),
]
