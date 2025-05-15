from django.urls import path
from . import views

app_name = 'main'  # here for namespacing of urls.

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('players/', views.player_list, name='player_list'),
    path('players/add/', views.player_create, name='player_add'),
    path('matches/<int:match_id>/add_stats/', views.match_add_stats, name='match_add_stats'),
    path('players/<int:pk>/', views.player_detail, name='player_detail'),
    path('players/<int:pk>/edit/', views.player_edit, name='player_edit'),
    path('players/<int:pk>/delete/', views.player_delete, name='player_delete'),

    path('matches/', views.match_list, name='match_list'),
    path('matches/add/', views.match_add, name='match_add'),
    path('matches/<int:pk>/', views.match_detail, name='match_detail'),
    path('matches/<int:pk>/edit/', views.match_edit, name='match_edit'),
    path('matches/<int:pk>/delete/', views.match_delete, name='match_delete'),

    path('staff/', views.staff_list, name='staff_list'),
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('meetings/', views.meeting_list, name='meeting_list'),
]
