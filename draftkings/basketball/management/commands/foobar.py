import numpy
# from matplotlib import pyplot as plt
from datetime import timedelta

from django.core.management.base import BaseCommand

from basketball.models import Season, GameLog, Game
import numpy as np
# import matplotlib.cm as cm

from basketball.utils.ann import NeuralNet
from basketball.utils.dk_tools.salaries import SalaryFileManager


def draw_teams_for_vs_against():
    myd = {}

    games = Game.objects.filter(season=Season.objects.get(name='16'))

    for game in games:
        gls_home = GameLog.objects.filter(game=game, team=game.home_team)
        gls_away = GameLog.objects.filter(game=game, team=game.away_team)

        home = str(game.home_team)
        away = str(game.away_team)

        pts_home = sum(_.draft_king_points for _ in gls_home)
        pts_away = sum(_.draft_king_points for _ in gls_away)

        if home in myd:
            myd[home]['scored'].append(pts_home)
            myd[home]['lost'].append(pts_away)
        else:
            myd[home] = {
                'scored': [pts_home],
                'lost': [pts_away]
            }

        if away in myd:
            myd[away]['scored'].append(pts_away)
            myd[away]['lost'].append(pts_home)
        else:
            myd[home] = {
                'scored': [pts_away],
                'lost': [pts_home]
            }

    for k, v in myd.items():
        scored = sum(myd[k]['scored']) / len(myd[k]['scored'])
        lost = sum(myd[k]['lost']) / len(myd[k]['lost'])
        myd[k]['bro'] = lost

        # plt.plot(lost, scored, marker='D')
        # plt.plot(pts_away, pts_home, marker='o')
        # plt.annotate(xy=(lost, scored), s=str(k))
        # plt.annotate(xy=(pts_away, pts_home), s=str(game.away_team))

        # plt.show()


class Command(BaseCommand):

    help = ''

    def add_arguments(self, parser):

        parser.add_argument(
            '-s', '--salary',
            action='store',
            type=int,
            help='Generate lineups using the specified salary file.')

    def handle(self, *args, **options):
        # draw_teams_for_vs_against()

        myd = {}

        games = Game.objects.filter(season=Season.objects.get(name='16'))

        for game in games:
            gls_home = GameLog.objects.filter(game=game, team=game.home_team)
            gls_away = GameLog.objects.filter(game=game, team=game.away_team)

            home = str(game.home_team)
            away = str(game.away_team)

            pts_home = sum(_.draft_king_points for _ in gls_home)
            pts_away = sum(_.draft_king_points for _ in gls_away)

            if home in myd:
                myd[home]['scored'].append(pts_home)
                myd[home]['lost'].append(pts_away)
            else:
                myd[home] = {
                    'scored': [pts_home],
                    'lost': [pts_away]
                }

            if away in myd:
                myd[away]['scored'].append(pts_away)
                myd[away]['lost'].append(pts_home)
            else:
                myd[home] = {
                    'scored': [pts_away],
                    'lost': [pts_home]
                }
        for k, v in myd.items():
            scored = sum(myd[k]['scored']) / len(myd[k]['scored'])
            lost = sum(myd[k]['lost']) / len(myd[k]['lost'])
            myd[k]['s'] = scored
            myd[k]['l'] = lost

        salary_file = SalaryFileManager.salary_files()[options.get('salary')]
        players = salary_file.from_db()
        date = salary_file.date()
        players = filter(lambda x: x.gamelog_set.filter(game__date=date).count() > 0, players)

        all_data = []
        min_scored = min([x['s'] for x in myd.values()])
        max_scored = max([x['s'] for x in myd.values()])

        min_lost = min([x['l'] for x in myd.values()])
        max_lost = max([x['l'] for x in myd.values()])

        def adjust_scored(val):
            return (val - min_scored) / float(max_scored - min_scored) * 0.999 + 0.0001

        def adjust_lost(val):
            return (val - min_lost) / float(max_lost - min_lost) * 0.999 + 0.0001

        max_ppm = max(gl.draft_king_points for gl in GameLog.objects.filter(game__season=Season.objects.get(name='16')))

        def adjust_ppm(val):
            return val / float(max_ppm) * 0.999 + 0.0001

        for player in players:
            gl = player.gamelog_set.get(game__date=date)
            home_team = gl.game.home_team
            away_team = gl.game.away_team
            avg_pts = player.average_points(game_logs=player.game_logs_last_x_days(120, from_date=date - timedelta(days=1)))
            opponent = home_team if home_team.pk != gl.team.pk else away_team
            all_data.append(
                [adjust_ppm(gl.draft_king_points), adjust_ppm(avg_pts),
                 adjust_scored(myd[gl.team.name]['s']), adjust_lost(myd[gl.team.name]['l']),
                 adjust_scored(myd[opponent.name]['s']), adjust_lost(myd[opponent.name]['l'])])

        input_nodes = len(all_data[0]) - 1
        hidden_nodes = 500
        output_nodes = 1
        learning_rate = 0.3

        # nn = NeuralNet(input_nodes, hidden_nodes, output_nodes, learning_rate)
        inputs = numpy.asfarray([x[1:] for x in all_data])
        targets = numpy.asfarray([x[:1] for x in all_data])

        # epochs = 5
        #
        # for i in range(epochs):
        #
        #     for x in range(len(inputs)):
        #         nn.train(inputs[x], targets[x])
        #
        # nn.query([0.7396911602209945, 0.4672634202234317, 0.44648171830433286, 0.4672634202234317, 0.44648171830433286])

        from sklearn.neural_network import MLPRegressor
        reg = MLPRegressor(hidden_layer_sizes=(10,), max_iter=1000)
        reg.fit(inputs, targets)
        predict = reg.predict(inputs[0])

        import ipdb; ipdb.set_trace()