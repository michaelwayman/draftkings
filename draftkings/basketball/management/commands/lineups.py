from collections import Counter, defaultdict
from datetime import timedelta
from django.core.management.base import BaseCommand

from basketball.utils.dk_tools.salaries import SalaryFileManager
from basketball.utils.evolution import Evolve
from basketball.models import Player


class Command(BaseCommand):

    help = ''

    def add_arguments(self, parser):

        parser.add_argument(
            '-s', '--salary',
            action='store',
            type=int,
            help='Generate lineups using the specified salary file.')

    def handle(self, *args, **options):

        if options.get('salary'):
            salary_file = SalaryFileManager.salary_files()[options.get('salary')]
            date = salary_file.date()
            contest_players = salary_file.player_salaries()
            players = Player.objects.filter(
                name__in=[cp.name for cp in contest_players]).exclude(name__in=INJURED_PLAYERS)

            # Assign the position and salary to each player from the DraftKing's Contest CSV
            for player in players:
                dk = filter(lambda k: k.name == player.name, contest_players)[0]
                player.position = dk.position
                player.salary = dk.salary

                # This is where we assign a player's value

                player.expected_points = player.estimated_points(dk.opponent, date=date, salary=player.salary)

            team_gl = defaultdict(list)
            team_top = dict()


            def ffilter(x):

                if x.salary <= 3300:
                    return False

                # if x.gamelog_set.filter(game__date=date).count() == 0:
                #     return False
                # else:
                #     if x.gamelog_set.filter(game__date=date)[0].draft_king_points == 0:
                #         return False

                gl = x.game_logs_last_x_days(10, from_date=date - timedelta(days=1))
                if gl.count() < 2:
                    return False

                ppm = sum(pm.points_per_min for pm in gl) / float(len(gl))

                avg_mins = x.average_minutes(game_logs=gl)
                if avg_mins < 18:
                    return False
                if ppm < 0.7:
                    return False

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
            evolve.run(750, n_print=None)

            print(evolve)


INJURED_PLAYERS = set(['Dwyane Wade', u'Markieff Morris', u'Mike Scott', u'Wayne Ellington', u'Paul Zipser', 'Rajon Rondo', 'D\'Angelo Russell', u'Willie Reed', u'Lance Thomas', u'Joakim Noah', u'Devin Harris', u'Jodie Meeks', u'Mike Miller', u'Justise Winslow', u'Alec Burks', u'Kevin Seraphin', u'Ivica Zubac', u'Ben Simmons', u'Joel Embiid', u'Nerlens Noel', u'Chandler Parsons', u'Khris Middleton', u'Deron Williams', u'Festus Ezeli', u'Jeremy Lamb', u'Brice Johnson', 'Jose Juan Barea', u'Mo Williams', u'Tiago Splitter', u'Tyreke Evans', u'Chris Bosh', u'Brandon Rush', u'Damian Jones', u'Nikola Pekovic', u'Reggie Jackson', u'Delon Wright', u'Derrick Favors', u'Tyson Chandler', u'George Hill', u'Lucas Nogueira', u'Cody Zeller', u'Jerryd Bayless', u'Ian Mahinmi', u'Treveon Graham', u'Jared Sullinger', u'Alexis Ajinca', u'Jeremy Lin', u'Caris LeVert', u'Gary Harris', u'Will Barton', u'Cameron Payne', u'Paul George', u'Brandan Wright', u'Doug McDermott', u'Quincy Pondexter', u'Dirk Nowitzki', u'Wesley Johnson', u'Michael Carter-Williams', 'Dewayne Dedmon', 'TJ Warren', u'Al-Farouq Aminu', 'CJ Miles'])
