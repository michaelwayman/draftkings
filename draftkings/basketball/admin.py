from django.contrib import admin

from .models import *


class GameLogAdmin(admin.ModelAdmin):
    list_display = ('player', 'game', 'minutes', 'draft_king_points',)
    list_filter = ('game__date', 'player__name',)


class GameAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'date', )
    ordering = ('date', )
    list_filter = ('player__name',)


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_team', 'position', 'average_points', 'average_minutes',)
    ordering = ('name', )
    list_filter = ('current_team__name',)


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'city',)
    ordering = ('name', )


admin.site.register(Player, PlayerAdmin)
admin.site.register(GameLog, GameLogAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register((Season, ))
admin.site.register(Contest)
admin.site.register(ContestPayout)
admin.site.register(Opponent)
admin.site.register(OpponentLineup)
