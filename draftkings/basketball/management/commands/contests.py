import logging as log

from django.core.management.base import BaseCommand
from texttable import Texttable

from basketball.models import Player, GameLog
from basketball.utils.contests import CSVManager as ContestManager


class Command(BaseCommand):

    help = (
        'Command to help manage the draftking contest CSV files. '
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
            help='Saves each contests salary to the database.')

    def handle(self, *args, **options):

        if options.get('list'):
            contests = ContestManager.contests()
            table = Texttable(max_width=100)
            table.set_deco(Texttable.HEADER)
            table.add_row(('#', 'File'))
            for i, cf in enumerate(contests):
                table.add_row((i + 1, cf.file_name))
            print(table.draw())

        if options.get('apply'):
            contest = ContestManager.contests()[options.get('apply') - 1]
            _apply_contest_information(contest)

        if options.get('apply_all'):
            for contest in ContestManager.contests():
                _apply_contest_information(contest)


def _apply_contest_information(contest):
    # for each player try to find their PlayerStat for a particular
    # game and update their salary to the database
    for player in contest.players():

        # try to find the PlayerStat in the database and update the salary.
        try:
            p = Player.objects.get(name=player.name)
            game_log = GameLog.objects.get(player=p, game__date=contest.date())
        except Player.DoesNotExist:
            log.warning(
                'Player {name} cannot be found.'.format(
                    name=player.name))
        except GameLog.DoesNotExist:
            log.warning(
                'GameLog for {name} on {date} cannot be found.'.format(
                    name=player.name,
                    date=contest.date()))
        else:
            game_log.dk_salary = player.salary
            game_log.save()
