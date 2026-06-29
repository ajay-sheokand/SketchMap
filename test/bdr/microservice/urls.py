from django.urls import path 
from . import views

app_name = 'microservice'
urlpatterns = [
    path('calculateLandmarksBDR/', views.calculateLandmarksBDR, name='calculateLandmarksBDR'),
    path('calculateJunctionsBDR/', views.calculateJunctionsBDR, name='calculateJunctionsBDR'),
]