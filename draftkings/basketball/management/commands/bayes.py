
from django.core.management.base import BaseCommand
from texttable import Texttable

from basketball.models import Season
from basketball.utils.dk_tools.salaries import SalaryFileManager


class Bcolors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Command(BaseCommand):

    help = (
        ''
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-s', '--salary',
            action='store',
            type=int,
            help='')
        parser.add_argument(
            '-S', '--season',
            action='store',
            type=str,
            help='')
        parser.add_argument(
            '-t', '--target',
            action='store',
            type=int,
            default=270,
            help='')

    def handle(self, *args, **options):

        salary_file = SalaryFileManager.salary_files()[options.get('salary')]
        date = salary_file.date()

        season = None
        if options.get('season'):
            season = Season.objects.get(name=options.get('season'))

        table = Texttable(max_width=180)
        table.set_deco(Texttable.HEADER)

        table_header = ('Player', '#games', 'salary', '0+', '15+', '20+', '25+', '30+',
                        '35+', '40+', '45+', '50+', '55+', '60+', '65+', '70+', '75+')

        c = 50000 / options.get('target')
        table_header_money = ('', '', '', '', c*15, c*20, c*25, c*30, c*35, c*40, c*45, c*50, c*55, c*60, c*65, c*70, c*75)

        table.add_row(table_header_money)
        table.add_row(table_header)
        values = []

        players = salary_file.players_from_db()
        for player in players:

            gl = player.game_logs_before_date(date)
            if season:
                gl = gl.filter(game__season=season)

            total_games = gl.count()

            if total_games == 0:
                continue

            games_group_0 = sum(1 for _ in gl if 0 <= _.draft_king_points) / float(total_games)
            games_group_1 = sum(1 for _ in gl if 15 <= _.draft_king_points) / float(total_games)
            games_group_2 = sum(1 for _ in gl if 20 <= _.draft_king_points) / float(total_games)
            games_group_3 = sum(1 for _ in gl if 25 <= _.draft_king_points) / float(total_games)
            games_group_4 = sum(1 for _ in gl if 30 <= _.draft_king_points) / float(total_games)
            games_group_5 = sum(1 for _ in gl if 35 <= _.draft_king_points) / float(total_games)
            games_group_6 = sum(1 for _ in gl if 40 <= _.draft_king_points) / float(total_games)
            games_group_7 = sum(1 for _ in gl if 45 <= _.draft_king_points) / float(total_games)
            games_group_8 = sum(1 for _ in gl if 50 <= _.draft_king_points) / float(total_games)
            games_group_9 = sum(1 for _ in gl if 55 <= _.draft_king_points) / float(total_games)
            games_group_10 = sum(1 for _ in gl if 60 <= _.draft_king_points) / float(total_games)
            games_group_11 = sum(1 for _ in gl if 65 <= _.draft_king_points) / float(total_games)
            games_group_12 = sum(1 for _ in gl if 70 <= _.draft_king_points) / float(total_games)
            games_group_13 = sum(1 for _ in gl if 75 <= _.draft_king_points) / float(total_games)

            groups = [games_group_0, games_group_1, games_group_2, games_group_3, games_group_4, games_group_5,
                      games_group_6, games_group_7, games_group_8, games_group_9, games_group_10, games_group_11,
                      games_group_12, games_group_13]

            # groups = [g if g > 0 and g != 1 else '' for g in groups]

            player_salary = None

            if gl.filter(game__date=date).count() > 0:

                player_salary = gl.get(game__date=date).dk_salary
                if player_salary < c*15:
                    group = 0
                elif c * 15 <= player_salary < c * 20:
                    group = 1
                elif c*20 <= player_salary < c*25:
                    group = 2
                elif c*25 <= player_salary < c*30:
                    group = 3
                elif c*30 <= player_salary < c*35:
                    group = 4
                elif c*35 <= player_salary < c*40:
                    group = 5
                elif c*40 <= player_salary < c*45:
                    group = 6
                elif c*45 <= player_salary < c*50:
                    group = 7
                elif c*50 <= player_salary < c*55:
                    group = 8
                elif c*55 <= player_salary < c*60:
                    group = 9
                elif c*60 <= player_salary < c*65:
                    group = 10
                elif c*65 <= player_salary < c*70:
                    group = 11
                elif c*70 <= player_salary < c*75:
                    group = 12
                elif c*75 <= player_salary:
                    group = 13

                groups[group] = Bcolors.OKGREEN + str(round(groups[group], 2)) + Bcolors.ENDC

            values.append([player.name, total_games, player_salary] + groups)

        # values = filter(lambda k: k[3] > 0.5, values)
        values = filter(lambda k: k[2], values)
        values.sort(key=lambda k: k[2], reverse=True)
        for v in values:
            table.add_row(v)
        table.add_row(table_header)
        print(table.draw())
        print('')
        print(len(values))
