from datetime import date
from django import forms
from .models import *
from django.core.exceptions import ValidationError

class PlayerForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Datum rođenja"
    )

    class Meta:
        model = Player
        fields = ['first_name', 'last_name', 'date_of_birth', 'position', 'category']
        labels = {
            'first_name': 'Ime',
            'last_name': 'Prezime',
            'position': 'Pozicija',
            'category': 'Kategorija',
        }

    def clean_category(self):
        category = self.cleaned_data.get('category')
        dob = self.cleaned_data.get('date_of_birth')
        
        if self.instance.pk:  
            history = self.instance.category_history.all().values_list('category', flat=True)
            previous_categories = set(history)

            cat_order = [c[0] for c in CATEGORIES]
            current_index = cat_order.index(category)

            for prev_cat in previous_categories:
                if cat_order.index(prev_cat) > current_index:
                    raise forms.ValidationError(f"Igrač se ne može vratiti u mlađu kategoriju ({dict(CATEGORIES)[prev_cat]} > {dict(CATEGORIES)[category]}).")


        if not category or not dob:
            return category  

        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        category_age_limits = {
            'U9': 9,
            'U11': 11,
            'MP': 13,
            'SP': 15,
            'JUN': 18,
            'SEN': 50,  
            'VET': 100,
        }

        max_age = category_age_limits.get(category)

        if age > max_age:
            raise forms.ValidationError(f"Igrač je prestar za kategoriju '{dict(CATEGORIES).get(category)}'.")

        return category

class MatchForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Datum utakmice")
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
        labels = {
            'date': 'Datum utakmice',
            'home_or_away': 'Domaćin ili gost',
            'opponent': 'Protivnik',
            'home_score': 'Golovi domaćina',
            'away_score': 'Golovi gosta',
            'category': 'Kategorija',
            'starting_players': 'Startna postava',
            'bench_players': 'Klupa',
            'captain': 'Kapetan',
            'goalkeeper': 'Golman',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'starting_players': forms.CheckboxSelectMultiple,
            'bench_players': forms.CheckboxSelectMultiple,
        }
    def __init__(self, *args, **kwargs):
        super(MatchForm, self).__init__(*args, **kwargs)

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
        labels = {
            'player': 'Igrač',
            'minute': 'Minuta',
            'event_type': 'Vrsta događaja',
        }
        
class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['player', 'minute']
        labels = {
            'player': 'Strijelac',
            'minute': 'Minuta',
        }
        widgets = {
            'minute': forms.NumberInput(attrs={'min': 0}),
        }

class AssistForm(forms.ModelForm):
    class Meta:
        model = Assist
        fields = ['player', 'minute']
        labels = {
            'player': 'Asistent',
            'minute': 'Minuta',
        }
        widgets = {
            'minute': forms.NumberInput(attrs={'min': 0}),
        }

class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['player', 'card_type', 'minute']
        labels = {
            'player': 'Igrač',
            'card_type': 'Vrsta kartona',
            'minute': 'Minuta',
        }
        widgets = {
            'minute': forms.NumberInput(attrs={'min': 0}),
            'card_type': forms.Select
        }
        
class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ['name', 'role', 'position', 'email', 'phone', 'active']
        labels = {
            'name': 'Ime i prezime',
            'role': 'Uloga',
            'position': 'Pozicija',
            'email': 'Email',
            'phone': 'Telefon',
            'active': 'Aktivan',
        }


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['date', 'title', 'notes', 'attendees']
        labels = {
            'date': 'Datum',
            'title': 'Naslov',
            'notes': 'Bilješke',
            'attendees': 'Sudionici',
        }
        widgets = {
            'attendees': forms.CheckboxSelectMultiple(),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'type', 'quantity', 'condition', 'purchase_date', 'description']
        labels = {
            'name': 'Naziv',
            'type': 'Vrsta',
            'quantity': 'Količina',
            'condition': 'Stanje',
            'purchase_date': 'Datum nabave',
            'description': 'Opis',
        }
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }