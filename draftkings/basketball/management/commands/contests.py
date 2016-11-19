import logging as log
import simplejson as json
import re

from os import listdir
from os.path import isfile, join

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from simplejson.scanner import JSONDecodeError

from basketball.constants import CONTEST_BATCH_DIR, CONTEST_PAGE_DIR
from basketball.models import Player, GameLog, Opponent, Contest, ContestPayout


class Command(BaseCommand):

    help = (
        ''
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-O', '--something',
            action='store_true',
            help='Reads in contest data'
        )

    def handle(self, *args, **options):

        if options.get('something'):
            contest_batch_files = [f for f in listdir(CONTEST_BATCH_DIR) if isfile(join(CONTEST_BATCH_DIR, f))]
            for file_name in contest_batch_files:
                if re.match('(\d{2}-\d{2}-\d{4}\.json)', file_name):
                    load_contest_data_by_day(f)

            contest_html_files = [f for f in listdir(CONTEST_PAGE_DIR) if isfile(join(CONTEST_PAGE_DIR, f))]

            # Remove invalid files
            contest_file_exp = re.compile('contest-([0-9]*).html')
            files = [f for f in contest_html_files if contest_file_exp.match(f)]

            for file_name in files:
                # pull id from file path
                dk_id = contest_file_exp.search(file_name).group(1)
                try:
                    contest = Contest.objects.get(dk_id=dk_id)
                    save_contest_payout_data(contest)
                except Contest.DoesNotExist:
                    log.warning('No contest with contest dk_id: {dk_id}'.format(
                        dk_id=dk_id
                    ))


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
        return contests


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


def save_contest_payout_data(contest):

    with open(join(CONTEST_PAGE_DIR, 'contest-2703870.html')) as file:
        soup = BeautifulSoup(file, 'html.parser')

    payout_rows = soup.find_all(class_='dk-grid')[-1:][0].contents
    payout_rows = [_.get_text() for _ in payout_rows if _ != u'\n']
    multi_range_exp = re.compile('([0-9]+)[strdhn]{2}[\s]-[\s]([0-9]{1,6})[strdhn]{0,2}.*\$([0-9]*.[0-9]*)')
    single_place_exp = re.compile('([0-9]+)[strdhn]{2}[$]([0-9]*.[0-9]*)')

    for row in payout_rows:
        row = row.replace('\n', '')
        if ' - ' in row:
            matches = multi_range_exp.search(row)
            start, stop, value = matches.group(1, 2, 3)
            ContestPayout.objects.create(contest=contest, start=start, stop=stop, value=value)
        else:
            matches = single_place_exp.search(row)
            start, stop, value = matches.group(1, 1, 2)
            ContestPayout.objects.create(contest=contest, start=start, stop=stop, value=value)

    for span in soup.find_all(class_='entrant-username'):
        user_name = span['title']
        Opponent.objects.create(user_name=user_name)
