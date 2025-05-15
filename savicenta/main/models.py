from django.db import models
from django.core.exceptions import ValidationError

class Player(models.Model):
    POSITION_CHOICES = [
        ('GK', 'Golman'),
        ('DF', 'Branič'),
        ('MF', 'Vezni'),
        ('FW', 'Napadač'),
    ]
    CATEGORY_CHOICES = [
        ('seniori', 'Seniori'),
        ('juniori', 'Juniori'),
        ('kadeti', 'Kadeti'),
        ('pioniri', 'Pioniri'),
    ]
    ime = models.CharField(max_length=100)
    prezime = models.CharField(max_length=100)
    datum_rodenja = models.DateField()
    pozicija = models.CharField(max_length=2, choices=POSITION_CHOICES)
    broj_dresa = models.IntegerField()
    kategorija = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.ime} {self.prezime}"

class StaffMember(models.Model):
    FUNKCIJE = [
        ('trener', 'Trener'),
        ('fizioterapeut', 'Fizioterapeut'),
        ('predstavnik', 'Predstavnik Kluba'),
    ]
    ime = models.CharField(max_length=100)
    funkcija = models.CharField(max_length=50, choices=FUNKCIJE)
    kontakt = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.funkcija.title()}: {self.ime}"

class Match(models.Model):
    datum = models.DateField()
    protivnik = models.CharField(max_length=100)
    lokacija = models.CharField(max_length=100)
    rezultat = models.CharField(max_length=20)
    opis = models.TextField(blank=True)
    igraci = models.ManyToManyField(Player, through='Statistics')
    kapetan = models.ForeignKey(Player, related_name='kapetan_utakmice', on_delete=models.SET_NULL, null=True)
    trener = models.ForeignKey(StaffMember, related_name='trener_utakmice', on_delete=models.SET_NULL, null=True, limit_choices_to={'funkcija': 'trener'})
    fizioterapeut = models.ForeignKey(StaffMember, related_name='fizio_utakmice', on_delete=models.SET_NULL, null=True, limit_choices_to={'funkcija': 'fizioterapeut'})
    predstavnik_kluba = models.ForeignKey(
        StaffMember,
        related_name='utakmice_kao_predstavnik',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Predstavnik kluba"
)

    def clean(self):
        if self.kapetan and not Statistics.objects.filter(utakmica=self, igrac=self.kapetan).exists():
            raise ValidationError("Kapetan mora biti među odabranim igračima za utakmicu.")

    def __str__(self):
        return f"{self.datum} - {self.protivnik}"

class Statistics(models.Model):
    igrac = models.ForeignKey(Player, on_delete=models.CASCADE)
    utakmica = models.ForeignKey(Match, on_delete=models.CASCADE)
    golovi = models.IntegerField(default=0)
    asistencije = models.IntegerField(default=0)
    minute = models.IntegerField(default=0)
    zuti_kartoni = models.IntegerField(default=0)
    crveni_kartoni = models.IntegerField(default=0)

    class Meta:
        unique_together = ('igrac', 'utakmica')

class Meeting(models.Model):
    datum = models.DateField()
    zapisnik = models.TextField()
    prisutni = models.ManyToManyField(StaffMember)

class Equipment(models.Model):
    naziv = models.CharField(max_length=100)
    kolicina = models.IntegerField()
    stanje = models.CharField(max_length=100)
    kategorija = models.CharField(max_length=100)
