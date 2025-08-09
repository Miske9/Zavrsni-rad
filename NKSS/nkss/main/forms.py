from datetime import date
from django.utils import timezone
from django import forms
from .models import *
from django.core.exceptions import ValidationError

class PlayerForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Datum rođenja"
    )
    
    member_since = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Član od",
        required=False
    )
    
    member_until = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Član do",
        required=False
    )

    class Meta:
        model = Player
        fields = ['first_name', 'last_name', 'date_of_birth', 'position', 'category', 
                  'is_active_member', 'member_since', 'member_until']
        labels = {
            'first_name': 'Ime',
            'last_name': 'Prezime',
            'position': 'Pozicija',
            'category': 'Kategorija',
            'is_active_member': 'Aktivan član',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If this is an existing player being reactivated
        if self.instance.pk and not self.instance.is_active_member:
            # Check membership history
            history = self.instance.membership_history.filter(
                action__in=['ACTIVATED', 'REACTIVATED']
            ).order_by('-created_at').first()
            
            if history:
                self.fields['member_since'].help_text = f"Bio član od {history.date_from.strftime('%d.%m.%Y')}"

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('is_active_member')
        member_since = cleaned_data.get('member_since')
        member_until = cleaned_data.get('member_until')
        
        # If activating a player
        if is_active:
            if not member_since:
                cleaned_data['member_since'] = date.today()
            
            # If there's an end date, it should be in the future
            if member_until and member_until < date.today():
                raise ValidationError("Datum završetka članstva ne može biti u prošlosti za aktivnog člana.")
        
        # If deactivating a player
        if not is_active and self.instance.pk:
            old_player = Player.objects.get(pk=self.instance.pk)
            if old_player.is_active_member and not member_until:
                # Set today as the end date if not specified
                cleaned_data['member_until'] = date.today()
        
        return cleaned_data

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

    def save(self, commit=True):
        player = super().save(commit=False)
        
        # Track if this is a reactivation
        if self.instance.pk:
            old_player = Player.objects.get(pk=self.instance.pk)
            
            # If reactivating
            if not old_player.is_active_member and player.is_active_member:
                # Keep the original member_since if it exists
                if old_player.member_since:
                    player.member_since = old_player.member_since
        
        if commit:
            player.save()
        
        return player

class MatchForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), 
        label="Datum utakmice",
        required=False  # Make it not required initially to avoid browser validation
    )
    starting_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Startna postava",
        required=False  # Make it not required initially
    )
    bench_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Klupa"
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
        
    def clean_date(self):
        date = self.cleaned_data['date']
        if date > timezone.localdate():
            raise forms.ValidationError("Datum ne može biti u budućnosti.")
        return date    

    def __init__(self, *args, **kwargs):
        super(MatchForm, self).__init__(*args, **kwargs)
        
        # Make fields not required initially to avoid browser validation
        self.fields['home_or_away'].required = False
        self.fields['opponent'].required = False
        self.fields['captain'].required = False
        self.fields['goalkeeper'].required = False

        category = None

        # Get category from instance, data, or initial
        if self.instance and self.instance.category:
            category = self.instance.category
        elif 'category' in self.data:
            category = self.data.get('category')
        elif self.initial.get('category'):
            category = self.initial.get('category')

        if category:
            # Filter players by category
            players = Player.objects.filter(category=category).order_by('last_name', 'first_name')
            self.fields['starting_players'].queryset = players
            self.fields['bench_players'].queryset = players
            self.fields['captain'].queryset = players
            self.fields['goalkeeper'].queryset = players
            
            # Make fields required when category is selected
            self.fields['date'].required = True
            self.fields['home_or_away'].required = True
            self.fields['opponent'].required = True
            self.fields['starting_players'].required = True
        else:
            # No players available without category
            self.fields['starting_players'].queryset = Player.objects.none()
            self.fields['bench_players'].queryset = Player.objects.none()
            self.fields['captain'].queryset = Player.objects.none()
            self.fields['goalkeeper'].queryset = Player.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        
        # Only validate if category is selected
        if category:
            starters = cleaned_data.get("starting_players")
            bench = cleaned_data.get("bench_players")
            captain = cleaned_data.get("captain")
            goalkeeper = cleaned_data.get("goalkeeper")
            home_score = cleaned_data.get("home_score", 0)
            away_score = cleaned_data.get("away_score", 0)
            
            # Required field validations
            if not cleaned_data.get("date"):
                self.add_error('date', "Datum utakmice je obavezan.")
            if not cleaned_data.get("home_or_away"):
                self.add_error('home_or_away', "Lokacija utakmice je obavezna.")
            if not cleaned_data.get("opponent"):
                self.add_error('opponent', "Naziv protivnika je obavezan.")

            # Player validations
            if starters and len(starters) != 11:
                raise ValidationError("Točno 11 igrača mora biti u startnoj postavi.")
            if bench and len(bench) > 7:
                raise ValidationError("Najviše 7 igrača može biti na klupi.")
            
            # Check for overlapping players
            if starters and bench:
                overlap = set(starters) & set(bench)
                if overlap:
                    player_names = [f"{p.first_name} {p.last_name}" for p in overlap]
                    raise ValidationError(f"Igrači ne mogu biti istovremeno u startnoj postavi i na klupi: {', '.join(player_names)}")
            
            if captain and starters and captain not in starters:
                raise ValidationError("Kapetan mora biti u startnoj postavi.")
            if goalkeeper and starters and goalkeeper not in starters:
                raise ValidationError("Golman mora biti u startnoj postavi.")

        return cleaned_data

    def validate_events(self, goal_formset, assist_formset, card_formset):
        """Validates match events - ensures goals match the score"""
        errors = []
        
        home_score = self.cleaned_data.get('home_score', 0)
        away_score = self.cleaned_data.get('away_score', 0)
        
        # Collect valid goals
        goals = []
        for form in goal_formset:
            if form.is_valid():
                player = form.cleaned_data.get('player')
                minute = form.cleaned_data.get('minute')
                # Only count if both player and minute are filled
                if player and minute:
                    goals.append(form.cleaned_data)
        
        # Check if number of goals matches the home score (our goals)
        if len(goals) != home_score:
            if home_score > 0:
                errors.append(f"Broj unesenih golova ({len(goals)}) mora odgovarati našem rezultatu ({home_score})")
            elif len(goals) > 0:
                errors.append(f"Uneseni su golovi ({len(goals)}) ali rezultat pokazuje 0 golova")
        
        # Collect valid assists  
        assists = []
        for form in assist_formset:
            if form.is_valid():
                player = form.cleaned_data.get('player')
                minute = form.cleaned_data.get('minute')
                # Only count if both player and minute are filled
                if player and minute:
                    assists.append(form.cleaned_data)
        
        # Assists can't be more than goals
        if len(assists) > len(goals):
            errors.append("Broj asistencija ne može biti veći od broja golova")
        
        # Check that each assist has a corresponding goal in the same minute
        if assists and goals:
            goal_minutes = [goal['minute'] for goal in goals]
            for assist in assists:
                if assist['minute'] not in goal_minutes:
                    errors.append(f"Asistencija u {assist['minute']}. minuti nema odgovarajući gol")
            
            # Check that a player can't assist their own goal in the same minute
            for assist in assists:
                same_minute_goals = [g for g in goals if g['minute'] == assist['minute']]
                for goal in same_minute_goals:
                    if goal['player'] == assist['player']:
                        errors.append(f"Igrač ne može asistirati svoj vlastiti gol u {assist['minute']}. minuti")
        
        return errors
        
        # Check that each assist has a corresponding goal in the same minute
        goal_minutes = [goal['minute'] for goal in goals]
        for assist in assists:
            if assist['minute'] not in goal_minutes:
                errors.append(f"Asistencija u {assist['minute']}. minuti nema odgovarajući gol")
        
        # Check that a player can't assist their own goal in the same minute
        for assist in assists:
            same_minute_goals = [g for g in goals if g['minute'] == assist['minute']]
            for goal in same_minute_goals:
                if goal['player'] == assist['player']:
                    errors.append(f"Igrač ne može asistirati svoj vlastiti gol u {assist['minute']}. minuti")
        
        return errors
    
class MatchEventForm(forms.ModelForm):
    class Meta:
        model = MatchEvent
        fields = ['player', 'minute', 'event_type']
        labels = {
            'player': 'Igrač',
            'minute': 'Minuta',
            'event_type': 'Vrsta događaja',
        }
        
class GoalEventForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.none(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    minute = forms.IntegerField(
        min_value=1, 
        max_value=120, 
        required=False, 
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minuta'})
    )
    
    def __init__(self, *args, **kwargs):
        valid_players = kwargs.pop('valid_players', Player.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['player'].queryset = valid_players

class AssistEventForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.none(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    minute = forms.IntegerField(
        min_value=1, 
        max_value=120, 
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minuta'})
    )
    
    def __init__(self, *args, **kwargs):
        valid_players = kwargs.pop('valid_players', Player.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['player'].queryset = valid_players

class CardEventForm(forms.Form):
    player = forms.ModelChoiceField(
        queryset=Player.objects.none(), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    card_type = forms.ChoiceField(
        choices=[('', '-- Odaberi --')] + list(CARD_TYPES), 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    minute = forms.IntegerField(
        min_value=1, 
        max_value=120, 
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minuta'})
    )
    
    def __init__(self, *args, **kwargs):
        valid_players = kwargs.pop('valid_players', Player.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['player'].queryset = valid_players
        
GoalFormSet = forms.formset_factory(GoalEventForm, extra=1, max_num=10, can_delete=True)
AssistFormSet = forms.formset_factory(AssistEventForm, extra=1, max_num=10, can_delete=True)
CardFormSet = forms.formset_factory(CardEventForm, extra=1, max_num=10, can_delete=True)
        
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