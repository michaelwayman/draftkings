from datetime import timedelta
from django.core.management.base import BaseCommand

from basketball.utils.contests import CSVManager as ContestManager
from basketball.utils.evolution import Evolve
from basketball.models import Player
from django.core.management import call_command


class Command(BaseCommand):

    help = ''

    def add_arguments(self, parser):
        parser.add_argument(
            '-l', '--list',
            action='store_true',
            help='List the contest CSV files.')
        parser.add_argument(
            '-c', '--contest',
            action='store',
            type=int,
            help='Generate lineups for the specified contest.')

    def handle(self, *args, **options):

        if options.get('list'):
            call_command('contests', '-l')
            return

        if options.get('contest'):
            contest = ContestManager.contests()[options.get('contest') - 1]
            date = contest.date()
            contest_players = contest.players()
            players = Player.objects.filter(
                name__in=[cp.name for cp in contest_players]).exclude(name__in=INJURED_PLAYERS)

            # Assign the position and salary to each player from the DraftKing's Contest CSV
            for player in players:
                dk = filter(lambda k: k.name == player.name, contest_players)[0]
                player.position = dk.position
                player.salary = dk.salary

                # This is where we assign a player's value
                player.expected_points = player.estimated_points(dk.opponent, date=date, salary=player.salary)

            def ffilter(x):
                if x.salary < 3200:
                    return False
                # try:
                #     x.gamelog_set.get(game__date=date)
                # except:
                #     return False
                # if x.gamelog_set.filter(game__date=date).count() == 0:
                #     return False
                # ppm = sum(pm.points_per_min for pm in gl)
                # if ppm < 0.9:
                #     return False
                return True

            # Available players for each position
            pgs = filter(lambda k: 'PG' in set(k.position.split('/')) and ffilter(k), players)
            sgs = filter(lambda k: 'SG' in set(k.position.split('/')) and ffilter(k), players)
            sfs = filter(lambda k: 'SF' in set(k.position.split('/')) and ffilter(k), players)
            pfs = filter(lambda k: 'PF' in set(k.position.split('/')) and ffilter(k), players)
            cs = filter(lambda k: 'C' in set(k.position.split('/')) and ffilter(k), players)
            gs = filter(lambda k: set(k.position.split('/')) & {'G', 'PG', 'SG'} and ffilter(k), players)
            fs = filter(lambda k: set(k.position.split('/')) & {'F', 'PF', 'SF'} and ffilter(k), players)
            utils = filter(lambda k: ffilter(k), players)

            position_lists = (pgs, sgs, sfs, pfs, cs, gs, fs, utils)

            print(len(position_lists[0]) * len(position_lists[1]) * len(position_lists[2]) * len(position_lists[3]) *
                  len(position_lists[4]) * len(position_lists[5]) * len(position_lists[6]) * len(position_lists[7]))

            evolve = Evolve({
                'pg': position_lists[0],
                'sg': position_lists[1],
                'sf': position_lists[2],
                'pf': position_lists[3],
                'c': position_lists[4],
                'g': position_lists[5],
                'f': position_lists[6],
                'util': position_lists[7],
            })

            evolve.date = date
            evolve.run(100000, n_print=10000)

            print(evolve)


INJURED_PLAYERS = set(['reke Evans', u'Mike Scott', u'Wayne Ellington', u'Pau Gasol', u'Anthony Davis', u'Dwight Howard',
                      u'Lance Thomas', u'Devin Harris', u'Jodie Meeks', u'LeBron James', u'Bradley Beal', u'Justise Winslow', u'Alec Burks',
                      u'Ben Simmons', u'Rodney Stuckey', u'Nikola Pekovic', u'Joel Embiid', u'Nerlens Noel', u'Chandler Parsons', u'Khris Middleton', u'Deron Williams', u'Festus Ezeli', u'Jeremy Lin', u'Brice Johnson', u'Mo Williams', u'Tiago Splitter', 'JR Smith', u'Patrick Beverley', u'Chris Bosh', u'Brandon Rush', u'Damian Jones', u'Goran Dragic', u'Reggie Jackson', u'Delon Wright', u'Derrick Favors', u'Rajon Rondo', u'George Hill', u'Jrue Holiday', u'Quincy Acy', u'Jae Crowder', u'Ian Mahinmi', u'Jared Sullinger', u'Darrell Arthur', u'Jeremy Lamb', u'Caris LeVert', u'Gary Harris', u'Danny Green', u'Will Barton', u'Shabazz Muhammad', u'Cameron Payne', u'Tony Allen', u'Brandan Wright', u'Doug McDermott', u'Quincy Pondexter', u'Dirk Nowitzki', u'Wesley Johnson', u'Michael Carter-Williams', 'Dewayne Dedmon', u'Al-Farouq Aminu', u'Al Horford', u'Wilson Chandler', u'Jerryd Bayless'])
