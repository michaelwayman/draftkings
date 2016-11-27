import logging as log

from django.core.management.base import BaseCommand
from texttable import Texttable

from basketball.models import Season, GameLog
from basketball.utils.dk_tools.salaries import SalaryFileManager
from basketball.utils.evolution import Evolve
from basketball.utils.roto.starters import StartersFileManager
from basketball.utils.statistics import PRManager, PRange


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


def assign_minutes(players, game_logs):

    for player in players:
        avg_mins = player.average_minutes(game_logs=game_logs)
        player.expected_minutes = avg_mins

        if hasattr(player, 'starting'):
            if player.starting:
                if str(player.name) in STARTERS_DONT_ADJUST_PLAYTIME:
                    continue
                if avg_mins < 20:
                    player.expected_minutes = 25
                    print('"{}" is starting. He averages {} minutes of playtime, setting to 25 mins.'.format(player.name, avg_mins))
            else:
                if avg_mins > 25:
                    player.expected_minutes = 20
                    print('"{}" is not starting. He averages {} minutes of playtime, settings to 20 mins.'.format(player.name, avg_mins))


def assign_points(players, game_logs):

    for player in players:
        avg_ppm = player.average_ppm(game_logs=game_logs)
        player.expected_points = avg_ppm * player.expected_minutes


def extra_filters(players, game_logs):

    players_to_remove = set()
    for player in players:
        avg_mins = player.average_minutes(game_logs=game_logs)
        avg_ppm = player.average_ppm(game_logs=game_logs)

        if hasattr(player, 'starting'):
            if player.starting is False:
                if avg_mins < 10:
                    players_to_remove.add(player)

        if avg_ppm < 0.8:
            players_to_remove.add(player)

    for player in players_to_remove:
        print('Removing "{}" for low expected yield'.format(str(player.name)))
        players.remove(player)


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

            injured_players = INJURED_PLAYERS
            starting_players = STARTING_PLAYERS

            # read in starters file and filter out injured players
            starters_file = StartersFileManager.starters_file_for_date(date)
            if starters_file is None:
                log.warning('Cannot find starters file, results may not be accurate.')
            else:
                injured_players |= starters_file.injured_players()
                starting_players |= starters_file.starting_players()
                players = filter(lambda k: k.name not in injured_players, players)
                for p in players:
                    p.starting = p.name in starting_players

            game_logs = GameLog.objects.filter(
                game__season=Season.objects.get(name='16'),
                game__date__lt=date)

            assign_minutes(players, game_logs)
            assign_points(players, game_logs)

            extra_filters(players, game_logs)

            players = filter(lambda x: x.gamelog_set.filter(game__date=date).count() > 0, players)

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
            evolve.run(50000, n_best=50)
            print(evolve)

            # Calculate and print the effectiveness of the generated lineups
            prmanager = PRManager([
                PRange(0, 250),
                PRange(250, 270),
                PRange(270, 300),
                PRange(300)])
            print('Results of {} lineups, with the top lineup at {}pts.'.format(
                len(evolve.best),
                max(_.actual for _ in evolve.best)))
            prmanager.calc_prange_probability(evolve.best, key=lambda k: k.actual)
            results_table = Texttable(max_width=80)
            results_table.set_deco(Texttable.HEADER)
            results_table.add_row(['points range', '% in range'])
            for rg in prmanager.pranges:
                results_table.add_row(['{} {}'.format(rg.d1, rg.d2 or '+'), int(rg.probability * 100)])
            print(results_table.draw())


INJURED_PLAYERS = set([])
STARTING_PLAYERS = set([])
STARTERS_DONT_ADJUST_PLAYTIME = set(['Zaza Pachulia'])
