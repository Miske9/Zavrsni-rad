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

]