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
            help='List the salary files.')
        parser.add_argument(
            '-s', '--save',
            action='store',
            type=int,
            help='Save the salary data from a particular file to the database.')
        parser.add_argument(
            '-S', '--save-all',
            action='store_true',
            help='Save all the salary files to the database.')

    def handle(self, *args, **options):

        if options.get('list'):
            salary_files = SalaryFileManager.salary_files()
            table = Texttable(max_width=100)
            table.set_deco(Texttable.HEADER)
            table.add_row(('#', 'File'))
            for i, sf in enumerate(salary_files):
                table.add_row((i, sf.file_name))
            print(table.draw())

        if options.get('save'):
            salary = SalaryFileManager.salary_files()[options.get('save')]
            salary.save_to_db()

        if options.get('save_all'):
            for salary_file in SalaryFileManager.salary_files():
                salary_file.save_to_db()
