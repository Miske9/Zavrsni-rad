from datetime import date
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

POSITIONS = [
    ("GK", "Goalkeeper"),
    ("DF", "Defender"),
    ("MF", "Midfielder"),
    ("FW", "Forward"),
]

CATEGORIES = [
    ("U9", "U9"),
    ("U11", "U11"),
    ("MP", "Mladi pioniri"),
    ("SP", "Stariji pioniri"),
    ("JUN", "Juniori"),
    ("SEN", "Seniori"),
    ("VET", "Veterani"),
]

CARD_TYPES = [
    ('Y', 'Yellow Card'),
    ('R', 'Red Card'),
]

class Player(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    position = models.CharField(max_length=2, choices=POSITIONS)
    category = models.CharField(max_length=3, choices=CATEGORIES, null=True, blank=True)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    appearances = models.PositiveIntegerField(default=0)
    is_active_member = models.BooleanField(default=True, verbose_name='Aktivan član')
    member_since = models.DateField(default=date.today, verbose_name='Član od')
    member_until = models.DateField(blank=True, null=True, verbose_name='Član do')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_membership_status(self):
        today = date.today()
        
        if self.is_active_member:
            if self.member_until and self.member_until >= today:
                return f"Aktivan član do {self.member_until.strftime('%d.%m.%Y')}"
            else:
                return "Aktivan član"
        else:
            if self.member_until and self.member_until > today:
                return f"Neaktivan (bio član, ponovno aktivan od {self.member_until.strftime('%d.%m.%Y')})"
            else:
                return "Neaktivan član"
    
    def save(self, *args, **kwargs):
        if self.pk:  
            old_player = Player.objects.get(pk=self.pk)
            if not old_player.is_active_member and self.is_active_member:
                MembershipHistory.objects.create(
                    player=self,
                    action='REACTIVATED',
                    date_from=date.today(),
                    date_until=self.member_until,
                    notes=f"Ponovno aktiviran {date.today().strftime('%d.%m.%Y')}"
                )
            elif old_player.is_active_member and not self.is_active_member:
                MembershipHistory.objects.create(
                    player=self,
                    action='DEACTIVATED',
                    date_from=old_player.member_since,
                    date_until=self.member_until or date.today(),
                    notes=f"Deaktiviran {date.today().strftime('%d.%m.%Y')}"
                )
        
        super().save(*args, **kwargs)
    
class PlayerCategoryHistory(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='category_history')
    category = models.CharField(max_length=3, choices=CATEGORIES)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player} - {self.get_category_display()} ({self.changed_at.date()})"

class MembershipHistory(models.Model):
    """Track membership changes for players"""
    ACTION_CHOICES = [
        ('ACTIVATED', 'Aktiviran'),
        ('DEACTIVATED', 'Deaktiviran'),
        ('REACTIVATED', 'Ponovno aktiviran'),
        ('EXTENDED', 'Produženo članstvo'),
    ]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='membership_history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    date_from = models.DateField()
    date_until = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Membership histories"
    
    def __str__(self):
        return f"{self.player} - {self.get_action_display()} ({self.created_at.date()})"


class Match(models.Model):
    HOME_AWAY = [("H", "Suhača"), ("A", "Gostovanje")]

    date = models.DateField()
    home_or_away = models.CharField(max_length=1, choices=HOME_AWAY)
    opponent = models.CharField(max_length=100)
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=3, choices=CATEGORIES)
    starting_players = models.ManyToManyField(Player, related_name="starts")
    bench_players = models.ManyToManyField(Player, related_name="bench", blank=True)
    captain = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, related_name="captain_matches")
    goalkeeper = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, related_name="goalkeeper_matches")

    def __str__(self):
        return f"{self.date} Smoljanci Sloboda vs {self.opponent} ({self.home_score}:{self.away_score})"

class MatchEvent(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    minute = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
    EVENT_TYPES = [
        ("GOAL", "Goal"),
        ("ASSIST", "Assist"),
        ("YC", "Yellow Card"),
        ("RC", "Red Card"),
    ]
    event_type = models.CharField(max_length=6, choices=EVENT_TYPES)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.event_type == "GOAL":
                self.player.goals += 1
            elif self.event_type == "ASSIST":
                self.player.assists += 1
            elif self.event_type == "YC":
                self.player.yellow_cards += 1
            elif self.event_type == "RC":
                self.player.red_cards += 1
            self.player.appearances += 1
            self.player.save()
        super().save(*args, **kwargs)

class StaffMember(models.Model):
    ROLE_TYPES = [
        ("U", "Uprava"),
        ("T", "Trener"),
        ("F", "Fizioterapeut"),
        ("O", "Ostalo"),
    ]

    name = models.CharField(max_length=100)
    role = models.CharField(max_length=1, choices=ROLE_TYPES)
    position = models.CharField(max_length=100, blank=True)  
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

class Meeting(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=200)
    notes = models.TextField()
    attendees = models.ManyToManyField(StaffMember, related_name='meetings_attended')

    def __str__(self):
        return f"Sastanak: {self.title} ({self.date})"

class Equipment(models.Model):
    EQUIPMENT_TYPES = [
        ("BALL", "Lopta"),
        ("KIT", "Dres"),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=4, choices=EQUIPMENT_TYPES)
    quantity = models.PositiveIntegerField()
    condition = models.CharField(max_length=50, default="Ispravno")
    purchase_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.name} ({self.quantity})"

class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals_scored')
    minute = models.PositiveIntegerField()

    def __str__(self):
        return f"Goal by {self.player} at {self.minute}'"

class Assist(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='assists')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='assists_made')
    minute = models.PositiveIntegerField()

    def __str__(self):
        return f"Assist by {self.player} at {self.minute}'"

class Card(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='cards')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='cards_received')
    card_type = models.CharField(max_length=1, choices=CARD_TYPES)
    minute = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.get_card_type_display()} for {self.player} at {self.minute}'"