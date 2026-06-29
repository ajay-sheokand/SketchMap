from django.urls import path
from . import views

app_name = 'generalizingmaps'
urlpatterns = [
    # path('mmReceiver/',views.mmGeoJsonReceiver),
    # path('smReceiver/',views.smGeoJsonReceiver),
    # path('analyzeInputMap/',views.analyzeInputMap),
    # path('requestFME/',views.requestFME),
    path('', views.map, name='map'),
    path('compare/', views.compare, name='compare'),
    path('compare/compareResults/', views.compareResults, name='compareResult')
]