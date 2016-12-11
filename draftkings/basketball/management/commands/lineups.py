import logging as log
from collections import Counter

from django.core.management.base import BaseCommand
from texttable import Texttable

from basketball.constants import TEAM_MAP
from basketball.models import Season, GameLog, Game, Team
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
                if avg_mins < 15:
                    player.expected_minutes += 10
                    print('"{}" is starting. He averages {} minutes of playtime, setting to 25 mins.'.format(player.name, avg_mins))
            else:
                if avg_mins > 27:
                    player.expected_minutes -= 7
                    print('"{}" is not starting. He averages {} minutes of playtime, settings to 20 mins.'.format(player.name, avg_mins))


def assign_points(players, game_logs):

    for player in players:
        avg_ppm = player.average_ppm(game_logs=game_logs)
        player.expected_points = avg_ppm * player.expected_minutes


def adjust_points(players):
    myd = {}

    games = Game.objects.filter(season=Season.objects.get(name='16'))

    for game in games:
        gls_home = GameLog.objects.filter(game=game, team=game.home_team)
        gls_away = GameLog.objects.filter(game=game, team=game.away_team)

        home = str(game.home_team)
        away = str(game.away_team)

        pts_home = sum(_.draft_king_points for _ in gls_home)
        pts_away = sum(_.draft_king_points for _ in gls_away)

        if home in myd:
            myd[home]['scored'].append(pts_home)
            myd[home]['lost'].append(pts_away)
        else:
            myd[home] = {
                'scored': [pts_home],
                'lost': [pts_away]
            }

        if away in myd:
            myd[away]['scored'].append(pts_away)
            myd[away]['lost'].append(pts_home)
        else:
            myd[home] = {
                'scored': [pts_away],
                'lost': [pts_home]
            }
    avg = 0
    for k, v in myd.items():
        scored = sum(myd[k]['scored']) / len(myd[k]['scored'])
        lost = sum(myd[k]['lost']) / len(myd[k]['lost'])
        myd[k]['bro'] = lost
        avg += lost

    avg /= float(len(myd))

    for player in players:
        try:
            player.opponent = Team.objects.get(abbreviation=TEAM_MAP.get(player.opponent, player.opponent)).name
        except:
            pass

    for player in players:
        # print(avg - myd[player.opponent]['bro'])
        if avg - myd[player.opponent]['bro'] > 1:
            player.expected_points *= 0.8
        elif avg - myd[player.opponent]['bro'] < -1:
            player.expected_points *= 1.2

    # print(myd)


def extra_filters(players, game_logs):

    players_to_remove = set()
    for player in players:
        avg_mins = player.average_minutes(game_logs=game_logs)
        avg_ppm = player.average_ppm(game_logs=game_logs)

        if player.salary < 3600:
            players_to_remove.add(player)

        if hasattr(player, 'starting'):
            if player.starting is False:
                if avg_mins < 14:
                    players_to_remove.add(player)

        if avg_ppm < 0.6:
            players_to_remove.add(player)

    print('\nRemoving players for low expected yield:')
    print(sorted([p.name for p in players_to_remove]))
    print('')
    for player in players_to_remove:
        players.remove(player)


def assign_actual_points(players, date):
    for player in players:
        gl = player.gamelog_set.get(game__date=date)
        player.expected_points = gl.draft_king_points


class Command(BaseCommand):

    help = ''

    def add_arguments(self, parser):

        parser.add_argument(
            '-s', '--salary',
            action='store',
            type=int,
            help='Generate lineups using the specified salary file.')
        parser.add_argument(
            '--make-csv',
            action='store',
            type=str,
            help='')

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

            print('\nInjured Players:')
            print(sorted(list(injured_players)))
            print('')
            print('\nStarters:')
            print(sorted(list(starting_players)))
            print('')

            game_logs = GameLog.objects.filter(
                game__season=Season.objects.get(name='16'),
                game__date__lt=date)

            assign_minutes(players, game_logs)
            assign_points(players, game_logs)

            extra_filters(players, game_logs)

            # adjust_points(players)

            # players = filter(lambda x: x.gamelog_set.filter(game__date=date).count() > 0, players)
            # assign_actual_points(players, date)

            # Map players to position
            positioned_players = map_players_to_positions(players)

            # Print some initialization information
            possible_lineups = 1
            for p in positioned_players.values():
                possible_lineups *= len(p)
            print('Generating lineups, about {} possible combinations.'.format(
                possible_lineups if possible_lineups > 1 else 0))

            # Generate the lineups and print them
            evolve = Evolve(positioned_players)
            evolve.date = date
            evolve.run(70000, n_best=5)
            print(evolve)

            if options.get('make_csv'):
                id_file = SalaryFileManager.id_file_for_date(date)
                id_file.apply_dk_ids(players)

                with open(options.get('make_csv'), 'w') as f:
                    f.write('PG,SG,SF,PF,C,G,F,UTIL\n')
                    for lineup in evolve.best:
                        out = [
                            lineup.genes['pg'].dk_id,
                            lineup.genes['sg'].dk_id,
                            lineup.genes['sf'].dk_id,
                            lineup.genes['pf'].dk_id,
                            lineup.genes['c'].dk_id,
                            lineup.genes['g'].dk_id,
                            lineup.genes['f'].dk_id,
                            lineup.genes['util'].dk_id]
                        f.write(','.join(out) + '\n')

            # Calculate and print the effectiveness of the generated lineups
            prmanager = PRManager([
                PRange(0, 250),
                PRange(250, 270),
                PRange(270, 300),
                PRange(300)])
            print('Results of top {} lineups with the best at {}pts.'.format(
                len(evolve.best),
                max(_.actual for _ in evolve.best)))
            prmanager.calc_prange_probability(evolve.best, key=lambda k: k.actual)
            results_table = Texttable(max_width=80)
            results_table.set_deco(Texttable.HEADER)
            results_table.add_row(['points range', '% in range'])
            for rg in prmanager.pranges:
                results_table.add_row(['{} {}'.format(rg.d1, rg.d2 or '+'), int(rg.probability * 100)])
            print(results_table.draw())

            p_dict = Counter()
            for lineup in evolve.best:
                for player in lineup.genes.values():
                    p_dict[player] += 1

            print(p_dict)


INJURED_PLAYERS = set([])
STARTING_PLAYERS = set([])
STARTERS_DONT_ADJUST_PLAYTIME = set([])
