from django.urls import path
from . import views

app_name = 'microservice'
urlpatterns = [
    path('requestFME/',views.requestFME),
]