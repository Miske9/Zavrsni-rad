from django import forms
from .models import Player, Match, MatchEvent, Goal, Assist, Card, StaffMember, Meeting, Equipment
from django.core.exceptions import ValidationError

class PlayerForm(forms.ModelForm):
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Player
        fields = ['first_name', 'last_name', 'date_of_birth', 'position', 'category']

class MatchForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    starting_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Startna postava (točno 11)"
    )
    bench_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Klupe (max 7)"
    )

    class Meta:
        model = Match
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'starting_players': forms.CheckboxSelectMultiple,
            'bench_players': forms.CheckboxSelectMultiple,
        }
    def __init__(self, *args, **kwargs):
        super(MatchForm, self).__init__(*args, **kwargs)

        # Ako postoji instanca i kategorija je definirana
        category = None

        if self.instance and self.instance.category:
            category = self.instance.category
        elif 'category' in self.data:
            category = self.data.get('category')

        if category:
            players = Player.objects.filter(category=category)
            self.fields['starting_players'].queryset = players
            self.fields['bench_players'].queryset = players
            self.fields['captain'].queryset = players
            self.fields['goalkeeper'].queryset = players
        else:
            self.fields['starting_players'].queryset = Player.objects.none()
            self.fields['bench_players'].queryset = Player.objects.none()
            self.fields['captain'].queryset = Player.objects.none()
            self.fields['goalkeeper'].queryset = Player.objects.none()
    def clean(self):
        cleaned_data = super().clean()
        starters = cleaned_data.get("starting_players")
        bench = cleaned_data.get("bench_players")
        captain = cleaned_data.get("captain")
        goalkeeper = cleaned_data.get("goalkeeper")

        if starters and len(starters) != 11:
            raise ValidationError("Točno 11 igrača mora biti u startnoj postavi.")
        if bench and len(bench) > 7:
            raise ValidationError("Najviše 7 igrača može biti na klupi.")
        if captain and captain not in starters:
            raise ValidationError("Kapetan mora biti u startnoj postavi.")
        if goalkeeper and goalkeeper not in starters:
            raise ValidationError("Golman mora biti u startnoj postavi.")

class MatchEventForm(forms.ModelForm):
    class Meta:
        model = MatchEvent
        fields = ['player', 'minute', 'event_type']
        
class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['player', 'minute']
        widgets = {
            'minute': forms.NumberInput(attrs={'min': 0}),
        }

class AssistForm(forms.ModelForm):
    class Meta:
        model = Assist
        fields = ['player', 'minute']
        widgets = {
            'minute': forms.NumberInput(attrs={'min': 0}),
        }

class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['player', 'card_type', 'minute']
        widgets = {
            'minute': forms.NumberInput(attrs={'min': 0}),
            'card_type': forms.Select
        }
        
class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ['name', 'role', 'position', 'email', 'phone', 'active']


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['date', 'title', 'notes', 'attendees']
        widgets = {
            'attendees': forms.CheckboxSelectMultiple(),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'type', 'quantity', 'condition', 'purchase_date', 'description']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }