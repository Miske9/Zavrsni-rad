from django import forms
from .models import Player, Match, StaffMember
from django.forms import ModelForm, modelformset_factory

class MatchForm(ModelForm):
    igraci = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Igrači (min 11, max 18)"
    )
    kapetan = forms.ModelChoiceField(
        queryset=Player.objects.all(),
        widget=forms.RadioSelect,
        label="Kapetan"
    )
    trener = forms.ModelChoiceField(queryset=StaffMember.objects.all(), label="Trener")
    fizioterapeut = forms.ModelChoiceField(queryset=StaffMember.objects.all(), label="Fizioterapeut")
    predstavnik = forms.ModelChoiceField(queryset=StaffMember.objects.all(), label="Predstavnik kluba")

    class Meta:
        model = Match
        fields = ['datum', 'protivnik', 'lokacija', 'rezultat', 'opis', 'igraci', 'kapetan', 'trener', 'fizioterapeut', 'predstavnik']

    def clean(self):
        cleaned_data = super().clean()
        igraci = cleaned_data.get('igraci')
        kapetan = cleaned_data.get('kapetan')

        if igraci:
            if len(igraci) < 11:
                self.add_error('igraci', 'Potrebno je odabrati najmanje 11 igrača.')
            if len(igraci) > 18:
                self.add_error('igraci', 'Možete odabrati najviše 18 igrača.')
            if kapetan and kapetan not in igraci:
                self.add_error('kapetan', 'Kapetan mora biti među odabranim igračima.')

        return cleaned_data
