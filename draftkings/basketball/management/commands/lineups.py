from collections import Counter
from datetime import timedelta
from django.core.management.base import BaseCommand

from basketball.utils.dk_tools.salaries import SalaryFileManager
from basketball.utils.evolution import Evolve
from basketball.models import Player


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
            salary_file = SalaryFileManager.salary_files()[options.get('salary')]
            date = salary_file.date()
            contest_players = salary_file.player_salaries()
            players = Player.objects.filter(
                name__in=[cp.name for cp in contest_players]).exclude(name__in=INJURED_PLAYERS)

            # Assign the position and salary to each player from the DraftKing's Contest CSV
            for player in players:
                dk = filter(lambda k: k.name == player.name, contest_players)[0]
                player.position = dk.position
                player.salary = dk.salary

                # This is where we assign a player's value

                player.expected_points = player.estimated_points(dk.opponent, date=date, salary=player.salary)

            team_gl = dict()
            team_top = dict()
            def ffilter(x):

                if x.salary <= 3200:
                    return False

                if x.gamelog_set.filter(game__date=date).count() == 0:
                    return False
                else:
                    if x.gamelog_set.filter(game__date=date)[0].draft_king_points == 0:
                        return False

                gl = x.game_logs_last_x_days(20, from_date=date - timedelta(days=1))
                ppm = sum(pm.points_per_min for pm in gl) / float(len(gl))

                avg_mins = x.average_minutes(game_logs=gl)
                if avg_mins < 16:
                    return False
                if ppm < 0.7:
                    return False

                if x.current_team not in team_gl:
                    team_gl[x.current_team] = x.current_team.game_logs_grouped_by_game()[:3]

                c = Counter()
                for game_logs in team_gl[x.current_team]:
                    for g in game_logs:
                        c[g.player] += g.minutes / 3.0

                if x.current_team not in team_top:
                    top_players = c.items()
                    top_players.sort(key=lambda k: k[1], reverse=True)
                    top_players = top_players[:8]
                    top_players = {_[0] for _ in top_players}
                    team_top[x.current_team] = top_players

                if x not in team_top[x.current_team]:
                    return False

                return True

            # Available players for each position
            pgs = filter(lambda k: 'PG' in set(k.position.split('/')) and ffilter(k), players)
            sgs = filter(lambda k: 'SG' in set(k.position.split('/')) and ffilter(k), players)
            sfs = filter(lambda k: 'SF' in set(k.position.split('/')) and ffilter(k), players)
            pfs = filter(lambda k: 'PF' in set(k.position.split('/')) and ffilter(k), players)
            cs = filter(lambda k: 'C' in set(k.position.split('/')) and ffilter(k), players)
            gs = filter(lambda k: set(k.position.split('/')) & {'G', 'PG', 'SG'} and ffilter(k), players)
            fs = filter(lambda k: set(k.position.split('/')) & {'F', 'PF', 'SF'} and ffilter(k), players)
            utils = filter(lambda k: ffilter(k), players)

            position_lists = (pgs, sgs, sfs, pfs, cs, gs, fs, utils)

            print(len(position_lists[0]) * len(position_lists[1]) * len(position_lists[2]) * len(position_lists[3]) *
                  len(position_lists[4]) * len(position_lists[5]) * len(position_lists[6]) * len(position_lists[7]))

            evolve = Evolve({
                'pg': position_lists[0],
                'sg': position_lists[1],
                'sf': position_lists[2],
                'pf': position_lists[3],
                'c': position_lists[4],
                'g': position_lists[5],
                'f': position_lists[6],
                'util': position_lists[7],
            })

            evolve.date = date
            evolve.run(500, n_print=None)

            print(evolve)


INJURED_PLAYERS = set()
