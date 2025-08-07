from datetime import date
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
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Datum utakmice")
    starting_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.none(),  # Ovo će se ažurirati u __init__
        widget=forms.CheckboxSelectMultiple,
        label="Startna postava (točno 11)"
    )
    bench_players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.none(),  # Ovo će se ažurirati u __init__
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
            # Filtriraj samo aktivne igrače iz određene kategorije
            players = Player.objects.filter(
                category=category,
                is_active_member=True
            ).exclude(
                member_until__lt=date.today()
            )
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
        home_score = cleaned_data.get("home_score", 0)
        away_score = cleaned_data.get("away_score", 0)

        # Provjeri da su svi igrači aktivni članovi
        all_players = list(starters or []) + list(bench or [])
        if captain:
            all_players.append(captain)
        if goalkeeper:
            all_players.append(goalkeeper)
            
        for player in all_players:
            if not player.is_current_member:
                raise ValidationError(f"Igrač {player.first_name} {player.last_name} nije aktivan član kluba.")

        if starters and len(starters) != 11:
            raise ValidationError("Točno 11 igrača mora biti u startnoj postavi.")
        if bench and len(bench) > 7:
            raise ValidationError("Najviše 7 igrača može biti na klupi.")
        if captain and captain not in starters:
            raise ValidationError("Kapetan mora biti u startnoj postavi.")
        if goalkeeper and goalkeeper not in starters:
            raise ValidationError("Golman mora biti u startnoj postavi.")

        return cleaned_data

    def validate_events(self, goal_formset, assist_formset, card_formset):
        """Validira događaje utakmice"""
        errors = []
        
        home_score = self.cleaned_data.get('home_score', 0)
        away_score = self.cleaned_data.get('away_score', 0)
        
        # Provjeri broj golova
        goals = []
        for form in goal_formset:
            if form.is_valid() and form.cleaned_data.get('player'):
                goals.append(form.cleaned_data)
        
        # Samo naši golovi se trebaju jednati s home_score (ako smo domaćin) ili away_score mora biti protivnikov
        if len(goals) != home_score:
            errors.append(f"Broj unesenih golova ({len(goals)}) mora odgovarati rezultatu ({home_score})")
        
        # Provjeri asistencije
        assists = []
        for form in assist_formset:
            if form.is_valid() and form.cleaned_data.get('player'):
                assists.append(form.cleaned_data)
        
        if len(assists) > len(goals):
            errors.append("Broj asistencija ne može biti veći od broja golova")
        
        # Provjeri da svaka asistencija ima odgovarajući gol u istoj minuti
        goal_minutes = [goal['minute'] for goal in goals]
        for assist in assists:
            if assist['minute'] not in goal_minutes:
                errors.append(f"Asistencija u {assist['minute']}. minuti nema odgovarajući gol")
        
        # Provjeri da igrač ne može asistirati svoj vlastiti gol u istoj minuti
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
    player = forms.ModelChoiceField(queryset=Player.objects.none(), required=False)
    minute = forms.IntegerField(min_value=1, max_value=120, required=False, 
                               widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minuta'}))
    
    def __init__(self, *args, **kwargs):
        valid_players = kwargs.pop('valid_players', Player.objects.none())
        super().__init__(*args, **kwargs)
        # Filtriraj samo aktivne igrače
        if valid_players:
            active_players = valid_players.filter(is_active_member=True).exclude(member_until__lt=date.today())
            self.fields['player'].queryset = active_players
        else:
            self.fields['player'].queryset = Player.objects.none()
        self.fields['player'].widget.attrs.update({'class': 'form-select'})

class AssistEventForm(forms.Form):
    player = forms.ModelChoiceField(queryset=Player.objects.none(), required=False)
    minute = forms.IntegerField(min_value=1, max_value=120, required=False,
                               widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minuta'}))
    
    def __init__(self, *args, **kwargs):
        valid_players = kwargs.pop('valid_players', Player.objects.none())
        super().__init__(*args, **kwargs)
        # Filtriraj samo aktivne igrače
        if valid_players:
            active_players = valid_players.filter(is_active_member=True).exclude(member_until__lt=date.today())
            self.fields['player'].queryset = active_players
        else:
            self.fields['player'].queryset = Player.objects.none()
        self.fields['player'].widget.attrs.update({'class': 'form-select'})

class CardEventForm(forms.Form):
    player = forms.ModelChoiceField(queryset=Player.objects.none(), required=False)
    card_type = forms.ChoiceField(choices=CARD_TYPES, required=False,
                                 widget=forms.Select(attrs={'class': 'form-select'}))
    minute = forms.IntegerField(min_value=1, max_value=120, required=False,
                               widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minuta'}))
    
    def __init__(self, *args, **kwargs):
        valid_players = kwargs.pop('valid_players', Player.objects.none())
        super().__init__(*args, **kwargs)
        # Filtriraj samo aktivne igrače
        if valid_players:
            active_players = valid_players.filter(is_active_member=True).exclude(member_until__lt=date.today())
            self.fields['player'].queryset = active_players
        else:
            self.fields['player'].queryset = Player.objects.none()
        
GoalFormSet = forms.formset_factory(GoalEventForm, extra=5, max_num=10)
AssistFormSet = forms.formset_factory(AssistEventForm, extra=5, max_num=10)
CardFormSet = forms.formset_factory(CardEventForm, extra=5, max_num=10)
        
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