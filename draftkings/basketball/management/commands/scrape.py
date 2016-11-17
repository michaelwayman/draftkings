
import gevent
from gevent import monkey

from basketball.models import Season

monkey.patch_socket()

from django.core.management.base import BaseCommand

from basketball.utils import db
from basketball.utils.datastruct_helpers import chunks
from basketball.utils.nba_scraper.scraper import (
    fetch_all_players,
    fetch_players_game_log,
    fetch_player_info,)


class Command(BaseCommand):

    help = 'Command for managing the nba_scraper and populating the database with the data it scrapes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--wipe-db',
            action='store_true',
            help='Clears the database before scraping.')
        parser.add_argument(
            '-c', '--chunks',
            action='store',
            type=int,
            default=30,
            help='Specify the number of gevents.')
        parser.add_argument(
            '-d', '--days',
            action='store',
            type=int,
            help='Scrape the current players last n days of game history.')
        parser.add_argument(
            '--misc',
            action='store_true',
            help='Whether or not to get player\'s misc data.')
        parser.add_argument(
            '-s', '--season',
            action='store',
            type=str,
            help='Scrape the data from the specified season.')
        parser.add_argument(
            '-A', '--all',
            action='store_true',
            help='Scrapes everything.')

    def handle(self, *args, **options):

        if options.get('wipe_db'):
            db.wipe_db()

        db.create_seasons()

        if options.get('days'):
            raise NotImplementedError

        if options.get('season'):
            try:
                season = Season.objects.get(name=options.get('season'))
            except Season.DoesNotExist:
                print('"{}" is not a valid season.'.format(options.get('season')))
                return
            scrape_by_season(season, options.get('chunks'), options.get('misc'))

        if options.get('all'):
            for season in Season.objects.all():
                scrape_by_season(season, options.get('chunks'), options.get('misc'))


def scrape_by_season(season, chunk_size, misc=False):
    all_players = fetch_all_players(season=season)
    number_of_players = len(all_players)
    counter = 0
    print('{} players total...'.format(number_of_players))
    print('0%')
    for all_p in chunks(all_players, chunk_size):

        jobs = []
        for player in all_p:
            jobs.append(gevent.spawn(fetch_players_game_log, player, season))
        gevent.wait(jobs)

        if misc:
            jobs = []
            for player in all_p:
                jobs.append(gevent.spawn(fetch_player_info, player))
            gevent.wait(jobs)

        counter += len(all_p)

        print('{}%'.format(int(counter / float(number_of_players) * 100.0)))

    print('done.')
