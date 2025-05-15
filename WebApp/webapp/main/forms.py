from django import forms
from .models import Player, Match

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = '__all__'

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = '__all__'

class MatchWithPlayersForm(MatchForm):
    starters = forms.ModelMultipleChoiceField(
        queryset=Player.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Igrači - Prva postava (11)"
    )
    substitutes = forms.ModelMultipleChoiceField(
        queryset=Player.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Igrači - Klupa (do 7)"
    )
    captain = forms.ModelChoiceField(
        queryset=Player.objects.none(),
        required=True,
        label="Kapetan"
    )

    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)

        if category:
            players = Player.objects.filter(category=category)
            self.fields['starters'].queryset = players
            self.fields['substitutes'].queryset = players
            self.fields['captain'].queryset = players

    def clean(self):
        cleaned_data = super().clean()
        starters = cleaned_data.get("starters")
        substitutes = cleaned_data.get("substitutes")
        captain = cleaned_data.get("captain")

        if starters.count() != 11:
            raise forms.ValidationError("Mora biti točno 11 igrača u prvoj postavi.")

        if substitutes.count() > 7:
            raise forms.ValidationError("Na klupi može biti najviše 7 igrača.")

        if captain not in starters and captain not in substitutes:
            raise forms.ValidationError("Kapetan mora biti među starterima ili na klupi.")

        # Provjera da je barem 1 golman među starterima
        gk_count = starters.filter(position='GK').count()
        if gk_count < 1:
            raise forms.ValidationError("Mora biti barem jedan golman u prvoj postavi.")