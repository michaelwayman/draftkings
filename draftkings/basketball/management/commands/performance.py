
from django.core.management.base import BaseCommand
from texttable import Texttable

from basketball.models import GameLog, Season
from basketball.utils import db
from basketball.utils.dk_tools.salaries import SalaryFileManager
from basketball.utils.elo import NBAManager as ELOManager
from basketball.utils.roto.starters import StartersFileManager
import logging as log

class Command(BaseCommand):

    help = (
        'Command to help manage the ELO algorithm.'
    )

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

            injured_players = set()
            starting_players = set()

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
            players = filter(lambda x: x.gamelog_set.filter(game__date=date).count() > 0, players)
            game_logs = GameLog.objects.filter(
                game__season=Season.objects.get(name='16'),
                game__date__lt=date)

            results_table = Texttable(max_width=180)
            results_table.set_deco(Texttable.HEADER)
            results_table.add_row(['Player', 'Pos', 'Team', 'Opponent', 'Avg mins', 'Mins', 'Avg pts', 'Pts', 'Starter', 'Diff'])
            results = []
            for player in players:
                gl = player.gamelog_set.get(game__date=date)
                avg_pts = player.average_points(game_logs=game_logs)
                avg_mins = player.average_minutes(game_logs=game_logs)
                avg_ppm = player.average_ppm(game_logs=game_logs)
                diff = gl.draft_king_points - avg_ppm * gl.minutes
                results.append(
                    (' '.join((player.name, str(player.salary))), ', '.join(player.position), gl.team.name, str(gl.game), avg_mins, gl.minutes, avg_pts, gl.draft_king_points, str(player.starting), diff))

            results.sort(key=lambda x: (x[2], x[-2]))

            for r in results:
                results_table.add_row(r)

            print(results_table.draw())
