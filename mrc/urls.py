from django.urls import path

from . import views

app_name = 'mrc'

urlpatterns = [
    path('', views.index, name='index'),
]
