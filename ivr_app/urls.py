from django.urls import path
from . import views

urlpatterns = [
    path('', views.voice_prompt, name='voice_prompt'),
    path('menu/', views.voice_menu, name='voice_menu'),
]
