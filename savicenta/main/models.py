
from django.db import models

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
    golovi = models.IntegerField(default=0)
    asistencije = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.ime} {self.prezime}"

class Match(models.Model):
    datum = models.DateField()
    protivnik = models.CharField(max_length=100)
    lokacija = models.CharField(max_length=100)
    rezultat = models.CharField(max_length=20)
    opis = models.TextField(blank=True)

class Statistics(models.Model):
    igrac = models.ForeignKey(Player, on_delete=models.CASCADE)
    utakmica = models.ForeignKey(Match, on_delete=models.CASCADE)
    golovi = models.IntegerField(default=0)
    asistencije = models.IntegerField(default=0)
    minute = models.IntegerField(default=0)
    zuti_kartoni = models.IntegerField(default=0)
    crveni_kartoni = models.IntegerField(default=0)

class StaffMember(models.Model):
    ime = models.CharField(max_length=100)
    funkcija = models.CharField(max_length=100)
    kontakt = models.CharField(max_length=100)

class Meeting(models.Model):
    datum = models.DateField()
    zapisnik = models.TextField()
    prisutni = models.ManyToManyField(StaffMember)

class Equipment(models.Model):
    naziv = models.CharField(max_length=100)
    kolicina = models.IntegerField()
    stanje = models.CharField(max_length=100)
    kategorija = models.CharField(max_length=100)
