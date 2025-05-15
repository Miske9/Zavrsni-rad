from django.contrib import admin
from .models import Player, Match, Goal, Assist, Card, MatchEvent
 
# Register your models here.
admin.site.register(Player)
admin.site.register(Match)
admin.site.register(Goal)
admin.site.register(Assist)
admin.site.register(Card)
admin.site.register(MatchEvent)
