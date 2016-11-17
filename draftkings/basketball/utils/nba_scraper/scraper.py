"""
NBA.com Data Scraper.

Functions to gather the player data required for the
 draftkings basketball app and populate the database with it.

"""

import datetime

import requests
import simplejson as json
from basketball.models import Team, Player, Game, GameLog
from basketball.utils.conversions import get_position_name, lb_to_kg, imperial_height_to_metric

from .config import *


def _build_url(path, qs):
    return '{scheme}://{host}{path}?{qs}'.format(
        scheme=SCHEME,
        host=HOST,
        path=path,
        qs='&'.join('{}={}'.format(key, val) for key, val in qs.items() if val)
    )


def fetch_all_players(season):
    """Calls NBA.com to get a list of all the players for a given season.

    Args:
        season: The `Season` whose players we want to get.

    Returns:
        A list of all the `Player`s.

    """
    # Our query string dict
    qs = ALL_PLAYERS_QS.copy()
    qs.update(
        Season=season.scrape_string())

    # Make the request
    response = requests.get(_build_url(ALL_PLAYERS, qs), headers=HEADERS)
    response.raise_for_status()

    # Load the data we got back into a list of `NBAPlayer`s
    results = [
        NBAPlayer(*row)
        for row in json.loads(response.content)['resultSets'][0]['rowSet']]

    return_value = []
    for r in results:

        # Skip if the player didn't play this season
        if int(r.to_year) < season.start_year():
            continue
        if int(r.from_year) > season.end_year():
            continue

        # Get or create the player's team
        try:
            team = Team.objects.get(scrape_id=r.team_id)
        except Team.DoesNotExist:
            team = Team.objects.create(
                scrape_id=r.team_id,
                city=r.team_city or 'None',
                name=r.team_name or 'None',
                abbreviation=r.team_abbreviation or 'None')

        # Get or create the player
        try:
            p = Player.objects.get(scrape_id=r.id)
        except Player.DoesNotExist:
            p = Player()

        # Update the player attrs and save.
        p.scrape_id = r.id
        p.name = r.name_first_last
        p.current_team = team
        p.save()

        return_value.append(p)
    return return_value


def fetch_players_game_log(player, season, from_date=None, to_date=None):
    """Calls NBA.com to get a players game history for a given season.

    Args:
        player: A `Player` whose game history we want to retrieve.
        season: The `Season` whose game log we want to get

    Returns:
        The game log of the player

    Note:
        This method will save the game log to the database.
        This method will create any `Game`s not in the database.
    """
    # Our query string dict
    qs = PLAYER_GAME_LOG_QS.copy()
    qs.update(
        PlayerID=player.scrape_id,
        Season=season.scrape_string())

    # Make the request
    response = requests.get(_build_url(PLAYER_GAME_LOG, qs), headers=HEADERS)
    response.raise_for_status()

    # Load the data we got back into a list of `NBAGameLog`s
    results = [
        NBAGameLog(*row)
        for row in json.loads(response.content)['resultSets'][0]['rowSet']]

    return_value = []
    for r in results:

        # Figure out who was playing.
        foo = r.matchup.split(' ')  # it looks like 'OKC vs. ORL' for home games and'OKC @ GSW' for away
        if '@' == foo[1]:
            home = False
            home_team = Team.objects.get(abbreviation=foo[2])
            away_team = Team.objects.get(abbreviation=foo[0])
        else:
            home = True
            home_team = Team.objects.get(abbreviation=foo[0])
            away_team = Team.objects.get(abbreviation=foo[2])

        # Get or create the `Game`
        try:
            game = Game.objects.get(scrape_id=r.game_id)
        except Game.DoesNotExist:
            game = Game.objects.create(
                scrape_id=r.game_id,
                season=season,
                date=datetime.datetime.strptime(r.game_date, "%b %d, %Y").date(),
                home_team=home_team,
                away_team=away_team)

        # Get or create the `GameLog`
        try:
            gl = GameLog.objects.get(player=player, game=game)
        except GameLog.DoesNotExist:
            gl = GameLog()

        # Update the GameLog and save()
        gl.player = player
        gl.game = game
        gl.team = home_team if home else away_team
        gl.minutes = r.min
        gl.field_goals_made = r.fgm
        gl.field_goals_attempted = r.fga
        gl.threes_made = r.fg3m
        gl.threes_attempted = r.fg3a
        gl.free_throws_made = r.ftm
        gl.free_throws_attempted = r.fta
        gl.twos_made = gl.field_goals_made - gl.threes_made
        gl.twos_attempted = gl.field_goals_attempted - gl.threes_attempted
        gl.offensive_rebounds = r.oreb
        gl.defensive_rebounds = r.dreb
        gl.assists = r.ast
        gl.steals = r.stl
        gl.blocks = r.blk
        gl.turnovers = r.tov
        gl.personal_fouls = r.pf
        gl.save()

        return_value.append(gl)

    return return_value


def fetch_player_info(player):
    """Calls NBA.com to get meta information about a given player.

    Args:
        player: The `Player` whose meta information we want.

    Returns:
        The player (for chained calls maybe? lol)

    Note:
        Updates player in the database with the meta information.
    """
    # Our query string dict
    qs = PLAYER_MISC_INFO_QS.copy()
    qs.update(PlayerID=player.scrape_id)

    # Make the request
    response = requests.get(_build_url(PLAYER_MISC_INFO, qs), headers=HEADERS)
    response.raise_for_status()

    # Load the data we got back into a `NBAPlayerMisc`
    r = NBAPlayerMisc(*json.loads(response.content)['resultSets'][0]['rowSet'][0])

    # Update the player in the db and save.
    player.birthday = r.birthdate.split('T')[0]
    player.height = imperial_height_to_metric(r.height)
    player.weight = lb_to_kg(r.weight)
    player.position = get_position_name(r.position)
    player.save()

    return player
