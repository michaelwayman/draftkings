import logging as log
import simplejson as json
import re

from os import listdir
from os.path import isfile, join

from django.core.management.base import BaseCommand
from simplejson.scanner import JSONDecodeError
from texttable import Texttable

from basketball.constants import CONTEST_BATCH_DIR
from basketball.models import Player, GameLog, Opponent, OpponentLineup, Contest
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
        parser.add_argument(
            '-O', '--something',
            action='store_true',
            help='Reads in contest data'
        )

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

        if options.get('something'):
            files = [f for f in listdir(CONTEST_BATCH_DIR) if isfile(join(CONTEST_BATCH_DIR, f))]
            for file in files:
                if re.match('(\d{2}-\d{2}-\d{4}\.json)', file):
                    load_contest_data_by_day(file)


def load_contest_data_by_day(file_name):
    with open(join(CONTEST_BATCH_DIR, file_name)) as content:
        try:
            contest_dict = json.load(content)
        except JSONDecodeError:
            log.warning(
                'Trouble decoding json file {file_name}'.format(
                    file_name=file_name))
            return
        contest_dicts = contest_dict['Contests']
        contests = [save_contest_data(contest) for contest in contest_dicts]


def save_contest_data(contest_dict):
    try:
        dk_id = contest_dict['id']
        name = contest_dict['n']
        entry_fee = contest_dict['a']
        entries_allowed = contest_dict['mec']
        total_entries = contest_dict['m']
        prize_pool = contest_dict['po']
    except KeyError:
        log.warning('Trouble extracting data from contest json {json}'.format(
            json=contest_dict
        ))
        return

    contest, created = Contest.objects.update_or_create(dk_id=dk_id, name=name, entry_fee=entry_fee,
                                                        mult_entries_allowed=entries_allowed,
                                                        total_entries=total_entries, prize_pool=prize_pool)
    return contest


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
