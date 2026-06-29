from django.urls import path
from . import views

app_name = 'microservice'
urlpatterns = [
    path('clearFiles/', views.clearFiles),
    path('mmReceiver/',views.mmGeoJsonReceiver),
    path('smReceiver/',views.smGeoJsonReceiver),
    path('analyzeQualitative/',views.analyzeQualitative),
]