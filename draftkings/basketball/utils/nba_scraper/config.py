"""
This file contains configuration settings used by the nba scraper

 - URL information
 - request headers
 - query string templates
 - named tuples that represent the information we expect back
 - example URLs for quick-reference and debugging
"""

from collections import namedtuple


# Basic information
HEADERS = {'user-agent': 'Mozilla/4.1 (Macintosh; Intel Mac OS X 10_8_1)'}
SCHEME = 'http'
HOST = 'stats.nba.com'

# Config to get all players for a particular season
# http://stats.nba.com/stats/commonallplayers?IsOnlyCurrentSeason=0&LeagueID=00&Season=2016-17
ALL_PLAYERS = '/stats/commonallplayers'

ALL_PLAYERS_QS = {
    'IsOnlyCurrentSeason': '0',
    'LeagueID': '00',
    'Season': 'change_me',
}

NBAPlayer = namedtuple(
    'AllPlayer', (
        'id',
        'name_last_comma_first',
        'name_first_last',
        'roster_status',
        'from_year',
        'to_year',
        'player_code',
        'team_id',
        'team_city',
        'team_name',
        'team_abbreviation',
        'team_code',
        'games_played_flag',))


# Config to get an individual player's game log for a particular season
# http://stats.nba.com/stats/playergamelog?LeagueID=00&PlayerID=201566&Season=2016-17&SeasonType=Regular+Season
PLAYER_GAME_LOG = '/stats/playergamelog'

PLAYER_GAME_LOG_QS = {
    'DateFrom': None,
    'DateTo': None,
    'LeagueID': '00',
    'PlayerID': 'change_me',
    'Season': 'change_me',
    'SeasonType': 'Regular+Season',
}

NBAGameLog = namedtuple(
    'NBAGameLog', (
        'season_id',
        'player_id',
        'game_id',
        'game_date',
        'matchup',
        'winloss',
        'min',
        'fgm',
        'fga',
        'fg_pct',
        'fg3m',
        'fg3a',
        'fg3_pct',
        'ftm',
        'fta',
        'ft_pct',
        'oreb',
        'dreb',
        'reb',
        'ast',
        'stl',
        'blk',
        'tov',
        'pf',
        'pts',
        'plus_minus',
        'video_available',))

# Config to get an individual player's miscellaneous information
# http://stats.nba.com/stats/commonplayerinfo?LeagueID=00&PlayerID=201566&SeasonType=Regular+Season
PLAYER_MISC_INFO = '/stats/commonplayerinfo'

PLAYER_MISC_INFO_QS = {
    'LeagueID': '00',
    'PlayerID': 'change_me',
    'SeasonType': 'Regular+Season',
}

NBAPlayerMisc = namedtuple(
    'NBAPlayerMisc', (
        'id',
        'name_first',
        'name_last',
        'name_first_last',
        'name_last_comma_first',
        'name_fi_last',
        'birthdate',
        'school',
        'country',
        'last_affiliation',
        'height',
        'weight',
        'season_exp',
        'jersey',
        'position',
        'roster_status',
        'team_id',
        'team_name',
        'team_abbreviation',
        'team_code',
        'team_city',
        'player_code',
        'from_year',
        'to_year',
        'dleague_flag',
        'games_played_flag',))
