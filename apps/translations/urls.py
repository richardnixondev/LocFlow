from django.urls import path

from apps.translations import views

urlpatterns = [
    path(
        "projects/<slug:slug>/strings/<uuid:string_id>/translations/",
        views.create_translation,
        name="translation-create",
    ),
    path(
        "projects/<slug:slug>/strings/<uuid:string_id>/translations/<str:language>/",
        views.update_translation,
        name="translation-update",
    ),
    path(
        "projects/<slug:slug>/progress/",
        views.translation_progress,
        name="translation-progress",
    ),
]
