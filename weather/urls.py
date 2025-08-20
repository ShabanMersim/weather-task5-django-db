from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/refresh_random/", views.api_refresh_random, name="api_refresh_random"),
    path("api/refresh_city/", views.api_refresh_city, name="api_refresh_city"),
    path("api/history/", views.api_history, name="api_history"),
]
