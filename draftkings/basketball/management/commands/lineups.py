import logging as log

from django.core.management.base import BaseCommand

from basketball.models import Season
from basketball.utils.dk_tools.salaries import SalaryFileManager
from basketball.utils.evolution import Evolve
from basketball.utils.roto.starters import StartersFileManager


def map_players_to_positions(players):
    return {
        'pg': filter(lambda k: 'PG' in k.position, players),
        'sg': filter(lambda k: 'SG' in k.position, players),
        'sf': filter(lambda k: 'SF' in k.position, players),
        'pf': filter(lambda k: 'PF' in k.position, players),
        'c': filter(lambda k: 'C' in k.position, players),
        'g': filter(lambda k: k.position & {'G', 'PG', 'SG'}, players),
        'f': filter(lambda k: k.position & {'F', 'PF', 'SF'}, players),
        'util': filter(lambda k: k, players)}


def assign_minutes(players, season=None):
    if season is None:
        season = Season.objects.get(name='16')

    for player in players:
        game_logs = player.game_logs_for_season(season).order_by('-game__date')
        avg_mins = player.average_minutes(game_logs=game_logs)
        player.expected_minutes = avg_mins

        if hasattr(player, 'starting'):
            if player.starting:
                if avg_mins < 20:
                    player.expected_minutes = 25
                    print('"{}" is starting. He averages {} minutes of playtime.'.format(player.name, avg_mins))
            else:
                if avg_mins > 25:
                    player.expected_minutes = 20
                    print('"{}" is not starting. He averages {} minutes of playtime.'.format(player.name, avg_mins))


def assign_points(players, season=None):
    if season is None:
        season = Season.objects.get(name='16')

    for player in players:
        game_logs = player.game_logs_for_season(season).order_by('-game__date')
        avg_ppm = player.average_ppm(game_logs=game_logs)
        player.expected_points = avg_ppm * player.expected_minutes


class Command(BaseCommand):

    help = ''

    def add_arguments(self, parser):

        parser.add_argument(
            '-s', '--salary',
            action='store',
            type=int,
            help='Generate lineups using the specified salary file.')

    def handle(self, *args, **options):

        if options.get('salary'):
            # Read in salary file and get players
            salary_file = SalaryFileManager.salary_files()[options.get('salary')]
            players = salary_file.from_db()
            date = salary_file.date()

            # read in starters file and filter out injured players
            starters_file = StartersFileManager.starters_file_for_date(date)
            if starters_file is None:
                log.warning('Cannot find starters file, results may not be accurate.')
            else:
                injured_players = starters_file.injured_players() | INJURED_PLAYERS
                starting_players = starters_file.starting_players() | STARTING_PLAYERS
                players = filter(lambda k: k.name not in injured_players, players)
                for p in players:
                    p.starting = p.name in starting_players

            assign_minutes(players)
            assign_points(players)

            # Map players to position
            positioned_players = map_players_to_positions(players)

            # Print some initialization information
            possible_lineups = 1
            for p in positioned_players.values():
                possible_lineups *= len(p)
            print('about {} possible lineup combinations.'.format(possible_lineups))

            # Generate the lineups
            evolve = Evolve(positioned_players)
            evolve.date = date
            evolve.run(2000, n_print=1000)
            print(evolve)


INJURED_PLAYERS = set()
STARTING_PLAYERS = set()
