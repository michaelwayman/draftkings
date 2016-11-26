from datetime import timedelta
from django.core.management.base import BaseCommand
from texttable import Texttable

from scipy.stats.stats import pearsonr

from basketball.models import Season, Game
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

    help = ('')

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
        parser.add_argument(
            '--min-games',
            action='store',
            type=int,
            default=10,
            help='')
        parser.add_argument(
            '-l', '--lineups',
            action='store_true',
            help='')
        parser.add_argument(
            '-p', '--print',
            action='store_true',
            help='')

    def handle(self, *args, **options):

        salary_file = SalaryFileManager.salary_files()[options.get('salary')]
        date = salary_file.date()

        season = None
        if options.get('season'):
            season = Season.objects.get(name=options.get('season'))

        players = salary_file.from_db()
        players = filter(
            lambda x: x.game_logs_before_date(date - timedelta(days=1)).filter(game__season=season).count() >= options.get('min_games'),
            players)
        # injured = set([u'Joe Johnson', u'Dario Saric', u'Mike Scott', u'Julius Randle', u'Paul Zipser', u'Dante Cunningham', u'Ian Mahinmi', u'Channing Frye', u'Lance Thomas', u'Joakim Noah', u'Devin Harris', u"D'Angelo Russell", u'Jodie Meeks', u'Nick Young', u'Mike Miller', u'Joel Embiid', u'Alec Burks', u'Kevin Seraphin', u'Zach Randolph', u'Ben Simmons', u'Rondae Hollis-Jefferson', u'Goran Dragic', u'Nerlens Noel', u'Chandler Parsons', u'Khris Middleton', u'Deron Williams', u'Festus Ezeli', u'Justise Winslow', u'Brice Johnson', 'Jose Juan Barea', u'Mo Williams', u'Nikola Pekovic', u'Willie Reed', u'Stanley Johnson', u'Tiago Splitter', u'Tyreke Evans', u'Chris Bosh', u'Damian Jones', u'Reggie Bullock', u'Danilo Gallinari', u'Reggie Jackson', u'Delon Wright', u'Derrick Favors', u'Wayne Ellington', u'James Ennis', u'Jared Sullinger', u'Jeremy Lin', u'Caris LeVert', u'Gary Harris', u'Will Barton', u'Cameron Payne', u'Paul George', u'Brandan Wright', u'Doug McDermott', u'Quincy Pondexter', u'Juan Hernangomez', u'Michael Carter-Williams', 'Dewayne Dedmon', 'TJ Warren', u'Al-Farouq Aminu', 'CJ Miles', u'Dion Waiters'])
        # players = filter(
        #     lambda x: x.name not in injured, players
        # )

        values = []
        for player in players:
            gl = player.game_logs_before_date(date - timedelta(days=1))
            if season is not None:
                gl = gl.filter(game__season=season)

            # gl = gl[:1]

            pmanager = PManager([
                RGroup(0, 5),
                RGroup(5, 10),
                RGroup(10, 15),
                RGroup(15, 20),
                RGroup(20, 25),
                RGroup(25, 30),
                RGroup(30, 35),
                RGroup(35, 40),
                RGroup(40, 45),
                RGroup(45, 50),
                RGroup(50, 55),
                RGroup(55, 60),
                RGroup(60),
            ])

            # team = gl[0].team
            # elo_diff = [_.game.elo_diff_for_team(team) for _ in gl]
            # pts = [pmanager.rgroups[pmanager.rgroup(_.draft_king_points)].d1 for _ in gl]
            #
            # elo_diff = Game.objects.games_for_team(team).get(date=date).elo_diff_for_team(team)
            # player.elo_diff = elo_diff
            correlation = '0'#str(pearsonr(pts, elo_diff)[0])
            pmanager.calc_rgroup_probability(gl, upper_bound=False, key=lambda x: x.draft_king_points)
            group = pmanager.rgroup(player.salary / (50000 / options.get('target')))
            if group >= 0:
                player.probability = pmanager.rgroups[group].probability
                player.expected_points = pmanager.rgroups[group].d1
            else:
                player.probability = 0.001
                player.expected_points = 0.001

            values.append(
                [player.name, player.salary, gl.count(), player.expected_points, correlation] + [_.probability for _ in pmanager.rgroups])

        if options.get('print'):
            table = Texttable(max_width=220)
            table.set_deco(Texttable.HEADER)
            table.add_row(['Player', 'Salary', '#Games', 'Target', 'Correlation'] + [_.d1 for _ in pmanager.rgroups])
            for v in values:
                table.add_row(v)
            print(table.draw())

        if options.get('lineups'):
            def ffilter(x):
                gl = x.game_logs_last_x_games(3, from_date=date - timedelta(days=1))
                gl_pts = x.game_logs_last_x_days(20, from_date=date - timedelta(days=1))
                avg_min = x.average_minutes(game_logs=gl)
                avg_pts = x.average_points(game_logs=gl_pts)
                if avg_min < 13:
                    return False
                # if x.expected_points <= 10:
                #     return False
                x.expected_points = avg_pts
                # if x.elo_diff > 50:
                #     x.probability *= 1.2
                # if x.elo_diff < -50:
                #     x.probability *= 0.8
                # avg_ppm = x.average_ppm(game_logs=gl)
                # if avg_ppm < 0.7:
                #     return False

                if x.salary <= 3000:
                    return False
                # if x.game_logs_last_x_days(90, from_date=date - timedelta(days=1)).count() < 7:
                #     return False
                # if x.probability < 0.2:
                #     return False
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
            # import ipdb; ipdb.set_trace()

            evolve.date = date
            evolve.run(5000, n_print=10000)

            print(evolve)

            lineups = evolve.best

            pmanager = PManager([
                RGroup(0, 150),
                RGroup(150, 200),
                RGroup(200, 225),
                RGroup(225, 250),
                RGroup(250, 275),
                RGroup(275, 300),
                RGroup(300),
            ])

            pmanager.calc_rgroup_probability(lineups, key=lambda k: k.actual)
            for rg in pmanager.rgroups:
                print('{}-{}    {}'.format(rg.d1, rg.d2, rg.probability))
            print('\n\n')

            pmanager = PManager([
                RGroup(0, 270),
                RGroup(270),])

            pmanager.calc_rgroup_probability(lineups, key=lambda k: k.actual)
            for rg in pmanager.rgroups:
                print('{}-{}    {}'.format(rg.d1, rg.d2, rg.probability))
