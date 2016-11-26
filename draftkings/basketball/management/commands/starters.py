
from django.core.management.base import BaseCommand
from texttable import Texttable

from basketball.utils.roto.starters import StartersFileManager, RotoScraper


class Command(BaseCommand):

    help = ''

    def add_arguments(self, parser):
        parser.add_argument(
            '-p', '--print',
            action='store',
            type=int,
            help='Print the sets of starters and injured players from a starter file.')
        parser.add_argument(
            '-l', '--list',
            action='store_true',
            help='Lists all the available starter files.')
        parser.add_argument(
            '-W', '--write',
            action='store',
            type=str,
            help='Pull the latest and write it to the given filename.')

    def handle(self, *args, **options):

        if options.get('list'):
            starter_files = StartersFileManager.starter_files()
            table = Texttable(max_width=100)
            table.set_deco(Texttable.HEADER)
            table.add_row(('#', 'File'))
            for i, sf in enumerate(starter_files):
                table.add_row((i, sf.file_name))
            print(table.draw())
            return

        if options.get('print') is not None:
            starter_file = StartersFileManager.starter_files()[options.get('print')]
            print('Starters:')
            print(set(starter_file.starting_players()))
            print('Injured:')
            print(set(starter_file.injured_players()))
            return

        if options.get('write'):
            print('Scraping from rotoworld..')
            starters, injured = RotoScraper.pull_data_from_roto()
            print('done.')
            print('Creating file..')
            StartersFileManager.create_starters_file(starters, injured, options.get('write'))
            print('done.')
