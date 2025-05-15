from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),

    # Player
    path('igraci/', views.PlayerListView.as_view(), name='player-list'),
    path('igraci/<int:pk>/', views.PlayerDetailView.as_view(), name='player-detail'),
    path('igraci/dodaj/', views.PlayerCreateView.as_view(), name='player-create'),
    path('igraci/<int:pk>/uredi/', views.PlayerUpdateView.as_view(), name='player-update'),
    path('igraci/<int:pk>/obrisi/', views.PlayerDeleteView.as_view(), name='player-delete'),

    # Match
    path('utakmice/', views.MatchListView.as_view(), name='match-list'),
    path('utakmice/<int:pk>/', views.MatchDetailView.as_view(), name='match-detail'),
    path('utakmice/dodaj/', views.MatchCreateView.as_view(), name='match-create'),
    path('utakmice/<int:pk>/uredi/', views.MatchUpdateView.as_view(), name='match-update'),
    path('utakmice/<int:pk>/obrisi/', views.MatchDeleteView.as_view(), name='match-delete'),

    # Staff
    path('uprava/', views.StaffListView.as_view(), name='staff-list'),
    path('uprava/<int:pk>/', views.StaffDetailView.as_view(), name='staff-detail'),
    path('uprava/dodaj/', views.StaffCreateView.as_view(), name='staff-create'),
    path('uprava/<int:pk>/uredi/', views.StaffUpdateView.as_view(), name='staff-update'),
    path('uprava/<int:pk>/obrisi/', views.StaffDeleteView.as_view(), name='staff-delete'),

    # Meeting
    path('sastanci/', views.MeetingListView.as_view(), name='meeting-list'),
    path('sastanci/<int:pk>/', views.MeetingDetailView.as_view(), name='meeting-detail'),
    path('sastanci/dodaj/', views.MeetingCreateView.as_view(), name='meeting-create'),
    path('sastanci/<int:pk>/uredi/', views.MeetingUpdateView.as_view(), name='meeting-update'),
    path('sastanci/<int:pk>/obrisi/', views.MeetingDeleteView.as_view(), name='meeting-delete'),

    # Equipment
    path('oprema/', views.EquipmentListView.as_view(), name='equipment-list'),
    path('oprema/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment-detail'),
    path('oprema/dodaj/', views.EquipmentCreateView.as_view(), name='equipment-create'),
    path('oprema/<int:pk>/uredi/', views.EquipmentUpdateView.as_view(), name='equipment-update'),
    path('oprema/<int:pk>/obrisi/', views.EquipmentDeleteView.as_view(), name='equipment-delete'),
] 