from django.contrib import admin
from .models import Player, Category, Match, MatchPlayer, PlayerMatchStat, StaffMember, Meeting, Equipment

admin.site.register(Player)
admin.site.register(Category)
admin.site.register(Match)
admin.site.register(MatchPlayer)
admin.site.register(PlayerMatchStat)
admin.site.register(StaffMember)
admin.site.register(Meeting)
admin.site.register(Equipment)
