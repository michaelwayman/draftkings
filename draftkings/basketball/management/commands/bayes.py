from datetime import timedelta
from django.core.management.base import BaseCommand

from basketball.models import Season
from basketball.utils.bayes import RGroup, PManager
from basketball.utils.dk_tools.salaries import SalaryFileManager
from basketball.utils.evolution import Evolve


class Bcolors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Command(BaseCommand):

    help = (
        ''
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-s', '--salary',
            action='store',
            type=int,
            help='')
        parser.add_argument(
            '-S', '--season',
            action='store',
            type=str,
            help='')
        parser.add_argument(
            '-t', '--target',
            action='store',
            type=int,
            default=270,
            help='')

    def handle(self, *args, **options):

        salary_file = SalaryFileManager.salary_files()[options.get('salary')]
        date = salary_file.date()

        season = None
        if options.get('season'):
            season = Season.objects.get(name=options.get('season'))

        players = salary_file.from_db()

        for player in players:
            gl = player.game_logs_before_date(date - timedelta(days=1))
            if season is not None:
                gl = gl.filter(game__season=season)

            pmanager = PManager([
                RGroup(0, 15),
                RGroup(15, 20),
                RGroup(20, 25),
                RGroup(25, 30),
                RGroup(30, 35),
                RGroup(35, 40),
                RGroup(40, 45),
                RGroup(45, 50),
                RGroup(50, 55),
                RGroup(55, 60),
                RGroup(60, 65),
                RGroup(70, 75),
                RGroup(80, 85),
            ])

            pmanager.calc_rgroup_probability(gl, upper_bound=False, key=lambda x: x.draft_king_points)
            group = pmanager.rgroup(player.salary / (50000 / options.get('target')))
            if group >= 0:
                player.probability = pmanager.rgroups[group].probability
                player.expected_points = pmanager.rgroups[group].d1
            else:
                player.probability = 0.001
                player.expected_points = 0.001

        def ffilter(x):
            if x.salary <= 3000:
                return False
            if x.game_logs_last_x_days(90, from_date=date - timedelta(days=1)).count() < 7:
                return False
            if x.probability < 0.3:
                return False
            if x.gamelog_set.filter(game__date=date).count() == 0:
                return False
            return True

        # Available players for each position
        pgs = filter(lambda k: 'PG' in k.position and ffilter(k), players)
        sgs = filter(lambda k: 'SG' in k.position and ffilter(k), players)
        sfs = filter(lambda k: 'SF' in k.position and ffilter(k), players)
        pfs = filter(lambda k: 'PF' in k.position and ffilter(k), players)
        cs = filter(lambda k: 'C' in k.position and ffilter(k), players)
        gs = filter(lambda k: k.position & {'G', 'PG', 'SG'} and ffilter(k), players)
        fs = filter(lambda k: k.position & {'F', 'PF', 'SF'} and ffilter(k), players)
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
        evolve.run(2000, n_print=10000)

        print(evolve)
