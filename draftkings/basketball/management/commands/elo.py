
from django.core.management.base import BaseCommand

from basketball.utils import db
from basketball.utils.elo import NBAManager as ELOManager


class Command(BaseCommand):

    help = (
        'Command to help manage the ELO algorithm.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-A', '--apply-all',
            action='store_true',
            help='Apply the ELO algorithm 1 game at a time using all historical data.')
        parser.add_argument(
            '-w', '--wipe-elo',
            action='store_true',
            help='Resets the ELO ranking to the initial state.')

    def handle(self, *args, **options):

        if options.get('wipe_elo'):
            print('Resetting ELO ranks.')
            db.reset_elo()
            print('Done.')

        if options.get('apply_all'):
            print('Calculating ELOs using all historical data.')
            ELOManager.apply_all_data()
            print('Done.')
