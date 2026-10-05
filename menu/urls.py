from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("", views.menu, name="menu"),
    path("buscar/", views.buscar, name="buscar"),
]