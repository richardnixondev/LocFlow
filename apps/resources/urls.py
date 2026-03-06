from django.urls import path

from apps.resources import views

urlpatterns = [
    path(
        "projects/<slug:slug>/upload/",
        views.upload_resource,
        name="resource-upload",
    ),
    path(
        "projects/<slug:slug>/resources/",
        views.list_resources,
        name="resource-list",
    ),
    path(
        "projects/<slug:slug>/strings/",
        views.list_strings,
        name="string-list",
    ),
    path(
        "projects/<slug:slug>/strings/<uuid:string_id>/",
        views.string_detail,
        name="string-detail",
    ),
    path(
        "projects/<slug:slug>/export/<str:language>/<str:file_format>/",
        views.export_translations,
        name="export-translations",
    ),
]
