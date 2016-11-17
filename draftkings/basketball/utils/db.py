"""
Miscellaneous helper methods for dealing with the database.
"""
from basketball.fixtures.seasons import NBASeasons
from basketball.models import Season, GameLog, Player, Game, GameManager, Team


def save(objs):
    """calls .save() on each object in objs"""
    for obj in objs:
        obj.save()


def wipe_db():
    """Wipes most of the data from the database."""
    for model in (Season, Player, Game, Team, GameLog, ):
        model.objects.all().delete()


def reset_elo():
    """Resets each each elo ranking to 1500"""
    for game in Game.objects.all():
        game.home_elo = 0
        game.away_elo = 0
        game.elo_applied = False
        game.save()

    for team in Team.objects.all():
        team.elo = 1500
        team.save()


def create_seasons():
    for data in NBASeasons:
        try:
            Season.objects.get(scrape_id=data['scrape_id'])
        except Season.DoesNotExist:
            s = Season()
            s.name = data['name']
            s.scrape_id = data['scrape_id']
            s.save()
