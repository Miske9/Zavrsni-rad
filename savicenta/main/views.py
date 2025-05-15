from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Player, Match, Statistics, StaffMember, Meeting, Equipment
from django.forms import ModelForm, ModelMultipleChoiceField, CheckboxSelectMultiple, ValidationError
from django import forms
from django.db.models import Sum

# INDEX

def index(request):
    return render(request, 'main/index.html')

# PLAYER
class PlayerListView(ListView):
    model = Player
    template_name = 'main/players/player_list.html'

class PlayerDetailView(DetailView):
    model = Player
    template_name = 'main/players/player_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        player = self.object
        stats = Statistics.objects.filter(igrac=player).select_related('utakmica')
        total_stats = stats.aggregate(
            ukupno_golova=Sum('golovi'),
            ukupno_asistencija=Sum('asistencije'),
            ukupno_zuti=Sum('zuti_kartoni'),
            ukupno_crveni=Sum('crveni_kartoni'),
            ukupno_minute=Sum('minute')
        )
        context['stats'] = stats
        context['total_stats'] = total_stats
        return context

class PlayerCreateView(CreateView):
    model = Player
    fields = '__all__'
    template_name = 'main/players/player_form.html'
    success_url = reverse_lazy('main:player-list')

class PlayerUpdateView(UpdateView):
    model = Player
    fields = '__all__'
    template_name = 'main/players/player_form.html'
    success_url = reverse_lazy('main:player-list')

class PlayerDeleteView(DeleteView):
    model = Player
    template_name = 'main/players/player_confirm_delete.html'
    success_url = reverse_lazy('main:player-list')

# MATCH FORM
class MatchForm(ModelForm):
    igraci = ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=CheckboxSelectMultiple,
        required=True
    )
    kapetan = forms.ModelChoiceField(queryset=Player.objects.all(), required=True)

    class Meta:
        model = Match
        fields = ['datum', 'protivnik', 'lokacija', 'rezultat', 'opis', 'trener', 'fizioterapeut', 'predstavnik_kluba', 'igraci', 'kapetan']

    def clean(self):
        cleaned_data = super().clean()
        igraci = cleaned_data.get('igraci')
        kapetan = cleaned_data.get('kapetan')
        if igraci:
            if len(igraci) < 11:
                raise ValidationError("Minimalno 11 igrača mora biti odabrano.")
            if len(igraci) > 18:
                raise ValidationError("Maksimalno 18 igrača može biti odabrano.")
            if kapetan and kapetan not in igraci:
                raise ValidationError("Kapetan mora biti jedan od odabranih igrača.")
        return cleaned_data

# MATCH
class MatchListView(ListView):
    model = Match
    template_name = 'main/matches/match_list.html'

class MatchDetailView(DetailView):
    model = Match
    template_name = 'main/matches/match_detail.html'

class MatchCreateView(CreateView):
    model = Match
    form_class = MatchForm
    template_name = 'main/matches/match_form.html'
    success_url = reverse_lazy('main:match-list')

class MatchUpdateView(UpdateView):
    model = Match
    form_class = MatchForm
    template_name = 'main/matches/match_form.html'
    success_url = reverse_lazy('main:match-list')

class MatchDeleteView(DeleteView):
    model = Match
    template_name = 'main/matches/match_confirm_delete.html'
    success_url = reverse_lazy('main:match-list')

# STATISTICS - za dodavanje statistike po utakmici
class StatisticsCreateView(CreateView):
    model = Statistics
    fields = '__all__'
    template_name = 'main/statistics/statistics_form.html'
    success_url = reverse_lazy('main:match-list')

class StatisticsUpdateView(UpdateView):
    model = Statistics
    fields = '__all__'
    template_name = 'main/statistics/statistics_form.html'
    success_url = reverse_lazy('main:match-list')

class StatisticsDeleteView(DeleteView):
    model = Statistics
    template_name = 'main/statistics/statistics_confirm_delete.html'
    success_url = reverse_lazy('main:match-list')

# STAFF
class StaffListView(ListView):
    model = StaffMember
    template_name = 'main/staff/staff_list.html'

class StaffDetailView(DetailView):
    model = StaffMember
    template_name = 'main/staff/staff_detail.html'

class StaffCreateView(CreateView):
    model = StaffMember
    fields = '__all__'
    template_name = 'main/staff/staff_form.html'
    success_url = reverse_lazy('main:staff-list')

class StaffUpdateView(UpdateView):
    model = StaffMember
    fields = '__all__'
    template_name = 'main/staff/staff_form.html'
    success_url = reverse_lazy('main:staff-list')

class StaffDeleteView(DeleteView):
    model = StaffMember
    template_name = 'main/staff/staff_confirm_delete.html'
    success_url = reverse_lazy('main:staff-list')

# MEETING
class MeetingListView(ListView):
    model = Meeting
    template_name = 'main/meetings/meeting_list.html'

class MeetingDetailView(DetailView):
    model = Meeting
    template_name = 'main/meetings/meeting_detail.html'

class MeetingCreateView(CreateView):
    model = Meeting
    fields = '__all__'
    template_name = 'main/meetings/meeting_form.html'
    success_url = reverse_lazy('main:meeting-list')

class MeetingUpdateView(UpdateView):
    model = Meeting
    fields = '__all__'
    template_name = 'main/meetings/meeting_form.html'
    success_url = reverse_lazy('main:meeting-list')

class MeetingDeleteView(DeleteView):
    model = Meeting
    template_name = 'main/meetings/meeting_confirm_delete.html'
    success_url = reverse_lazy('main:meeting-list')

# EQUIPMENT
class EquipmentListView(ListView):
    model = Equipment
    template_name = 'main/equipment/equipment_list.html'

class EquipmentDetailView(DetailView):
    model = Equipment
    template_name = 'main/equipment/equipment_detail.html'

class EquipmentCreateView(CreateView):
    model = Equipment
    fields = '__all__'
    template_name = 'main/equipment/equipment_form.html'
    success_url = reverse_lazy('main:equipment-list')

class EquipmentUpdateView(UpdateView):
    model = Equipment
    fields = '__all__'
    template_name = 'main/equipment/equipment_form.html'
    success_url = reverse_lazy('main:equipment-list')

class EquipmentDeleteView(DeleteView):
    model = Equipment
    template_name = 'main/equipment/equipment_confirm_delete.html'
    success_url = reverse_lazy('main:equipment-list')
