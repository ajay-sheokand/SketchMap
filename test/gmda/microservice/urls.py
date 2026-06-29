from django.urls import path 
from . import views

app_name = 'microservice'
urlpatterns = [
    path('calculateGMDA/', views.calculateGMDA, name='calculateGMDA'),
    path('calculateJunctionGMDA/', views.calculateJunctionGMDA, name='calculateJunctionGMDA'),
]