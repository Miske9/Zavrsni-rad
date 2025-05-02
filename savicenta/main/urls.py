from django.urls import path
from . import views

app_name = 'main'
# URL patterns for the main app

urlpatterns = [
    path('', views.index, name='index'),
    # Player
    path('players/', views.PlayerListView.as_view(), name='player-list'),
    path('players/<int:pk>/', views.PlayerDetailView.as_view(), name='player-detail'),
    path('players/create/', views.PlayerCreateView.as_view(), name='player-create'),
    path('players/<int:pk>/update/', views.PlayerUpdateView.as_view(), name='player-update'),
    path('players/<int:pk>/delete/', views.PlayerDeleteView.as_view(), name='player-delete'),

    # Match
    path('matches/', views.MatchListView.as_view(), name='match-list'),
    path('matches/<int:pk>/', views.MatchDetailView.as_view(), name='match-detail'),
    path('matches/create/', views.MatchCreateView.as_view(), name='match-create'),
    path('matches/<int:pk>/update/', views.MatchUpdateView.as_view(), name='match-update'),
    path('matches/<int:pk>/delete/', views.MatchDeleteView.as_view(), name='match-delete'),

    # Statistics
    path('statistics/', views.StatisticsListView.as_view(), name='statistics-list'),
    path('statistics/<int:pk>/', views.StatisticsDetailView.as_view(), name='statistics-detail'),
    path('statistics/create/', views.StatisticsCreateView.as_view(), name='statistics-create'),
    path('statistics/<int:pk>/update/', views.StatisticsUpdateView.as_view(), name='statistics-update'),
    path('statistics/<int:pk>/delete/', views.StatisticsDeleteView.as_view(), name='statistics-delete'),

    # Staff
    path('staff/', views.StaffListView.as_view(), name='staff-list'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff-detail'),
    path('staff/create/', views.StaffCreateView.as_view(), name='staff-create'),
    path('staff/<int:pk>/update/', views.StaffUpdateView.as_view(), name='staff-update'),
    path('staff/<int:pk>/delete/', views.StaffDeleteView.as_view(), name='staff-delete'),

    # Meeting
    path('meetings/', views.MeetingListView.as_view(), name='meeting-list'),
    path('meetings/<int:pk>/', views.MeetingDetailView.as_view(), name='meeting-detail'),
    path('meetings/create/', views.MeetingCreateView.as_view(), name='meeting-create'),
    path('meetings/<int:pk>/update/', views.MeetingUpdateView.as_view(), name='meeting-update'),
    path('meetings/<int:pk>/delete/', views.MeetingDeleteView.as_view(), name='meeting-delete'),

    # Equipment
    path('equipment/', views.EquipmentListView.as_view(), name='equipment-list'),
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment-detail'),
    path('equipment/create/', views.EquipmentCreateView.as_view(), name='equipment-create'),
    path('equipment/<int:pk>/update/', views.EquipmentUpdateView.as_view(), name='equipment-update'),
    path('equipment/<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='equipment-delete'),
]
