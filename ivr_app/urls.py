from django.urls import path
from . import views

urlpatterns = [
    path('', views.voice_prompt, name='voice_prompt'),
    path('menu/', views.voice_menu, name='voice_menu'),
    path('auto_first/', views.voice_auto_first, name='voice_auto_first'),
    path('status/', views.voice_status, name='voice_status'),
]
