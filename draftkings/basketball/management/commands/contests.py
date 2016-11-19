import logging as log

from django.core.management.base import BaseCommand
from texttable import Texttable

from basketball.models import Player, GameLog
from basketball.utils.dk_tools.salaries import SalaryFileManager


class Command(BaseCommand):

    help = (
        'Command to help manage the draftking salary files. '
        'At some point you need to assign the draftking salaries for each player '
        'to the database and this command helps to do that.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-l', '--list',
            action='store_true',
            help='List the contest CSV files.')
        parser.add_argument(
            '-a', '--apply',
            action='store',
            type=int,
            help='Apply the contest data from a particular file.')
        parser.add_argument(
            '-A', '--apply-all',
            action='store_true',
            help='Saves each salary to the database.')

    def handle(self, *args, **options):

        if options.get('list'):
            salary_files = SalaryFileManager.salary_files()
            table = Texttable(max_width=100)
            table.set_deco(Texttable.HEADER)
            table.add_row(('#', 'File'))
            for i, sf in enumerate(salary_files):
                table.add_row((i, sf.file_name))
            print(table.draw())

        if options.get('apply'):
            salary = SalaryFileManager.salary_files()[options.get('apply')]
            _apply_salary_file_information(salary)

        if options.get('apply_all'):
            for salary_file in SalaryFileManager.salary_files():
                _apply_salary_file_information(salary_file)


def _apply_salary_file_information(salary_file):
    # for each player try to find their PlayerStat for a particular
    # game and update their salary to the database
    for player in salary_file.player_salaries():

        # try to find the PlayerStat in the database and update the salary.
        try:
            p = Player.objects.get(name=player.name)
            game_log = GameLog.objects.get(player=p, game__date=salary_file.date())
        except Player.DoesNotExist:
            log.warning(
                'Player {name} cannot be found.'.format(
                    name=player.name))
        except GameLog.DoesNotExist:
            log.warning(
                'GameLog for {name} on {date} cannot be found.'.format(
                    name=player.name,
                    date=salary_file.date()))
        else:
            game_log.dk_salary = player.salary
            game_log.save()
