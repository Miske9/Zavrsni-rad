from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path('', views.index, name='index'),
    # Player
    path("players/", views.player_list, name="player_list"),
    path("players/add/", views.player_create, name="player_create"),
    path("players/<int:pk>/", views.player_detail, name="player_detail"),
    path("players/<int:pk>/edit/", views.player_update, name="player_update"),
    path("players/<int:pk>/delete/", views.player_delete, name="player_delete"),

    # Match
    path("matches/", views.match_list, name="match_list"),
    path("matches/add/", views.match_create, name="match_create"),
    path("matches/<int:pk>/", views.match_detail, name="match_detail"),
    path("matches/<int:pk>/edit/", views.match_update, name="match_update"),
    path("matches/<int:pk>/delete/", views.match_delete, name="match_delete"),
    path('matches/<int:match_id>/add_goal/', views.add_goal, name='add_goal'),
    path('matches/<int:match_id>/add_assist/', views.add_assist, name='add_assist'),
    path('matches/<int:match_id>/add_card/', views.add_card, name='add_card'),
    
    path('staff/', views.staffmember_list, name='staffmember-list'),
    path('staff/<int:pk>/', views.staffmember_detail, name='staffmember_detail'),
    path('staff/create/', views.staffmember_create, name='staffmember_create'),
    path('staff/<int:pk>/update/', views.staffmember_update, name='staffmember_update'),
    path('staff/<int:pk>/delete/', views.staffmember_delete, name='staffmember_delete'),

    # Meeting urls
    path('meetings/', views.meeting_list, name='meeting-list'),
    path('meetings/<int:pk>/', views.meeting_detail, name='meeting_detail'),
    path('meetings/create/', views.meeting_create, name='meeting_create'),
    path('meetings/<int:pk>/update/', views.meeting_update, name='meeting_update'),
    path('meetings/<int:pk>/delete/', views.meeting_delete, name='meeting_delete'),

    # Equipment urls
    path('equipment/', views.equipment_list, name='equipment-list'),
    path('equipment/<int:pk>/', views.equipment_detail, name='equipment_detail'),
    path('equipment/create/', views.equipment_create, name='equipment_create'),
    path('equipment/<int:pk>/update/', views.equipment_update, name='equipment_update'),
    path('equipment/<int:pk>/delete/', views.equipment_delete, name='equipment_delete'),

]