from datetime import timedelta
from django.core.management.base import BaseCommand
from texttable import Texttable

from basketball.models import Team, Player, Season, GameLog
from basketball.utils.ann.ann import NeuralNet


class Command(BaseCommand):

    help = (
        'Command to help manage the ANN.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-lt', '--list-teams',
            action='store_true',
            help='')
        parser.add_argument(
            '-p', '--print',
            action='store',
            type=int,
            help='print the ann stuff.')
        parser.add_argument(
            '-mtd', '--make-training-data',
            action='store',
            type=int,
            help='print the ann stuff.')

    def handle(self, *args, **options):

        teams = Team.objects.all().order_by('name')

        if options.get('list_teams'):
            table = Texttable(max_width=100)
            table.set_deco(Texttable.HEADER)
            table.add_row(('#', 'Team'))
            for i, team in enumerate(teams):
                table.add_row((i, team.name))
            print(table.draw())

        if options.get('print') >= 0:
            pass

        if options.get('make_training_data'):
            input = options.get('make_training_data')
            team = teams[input]

            game_logs = team.game_logs_grouped_by_game(game_logs=GameLog.objects.filter(team=team))
            from itertools import chain
            players = Player.objects.filter(pk__in=[_.player.pk for _ in chain(*game_logs)])

            ret_mins = []
            ret_play = []
            ret_avg = []
            ret_gl = []
            for gl in game_logs:
                minutes = []
                played = []
                averages = []
                for player in players:
                    l = filter(lambda k: k.player.pk == player.pk, gl)
                    val = sum([_.minutes for _ in l])
                    minutes.append(val)

                    played.append(0 if val == 0 else 1)
                    game_logs = player.game_logs_last_x_days(15, from_date=gl[0].game.date - timedelta(days=1))
                    avg = player.average_minutes(game_logs=game_logs)
                    if val == 0:
                        avg = 0
                    averages.append(avg)

                ret_mins.append(minutes)
                ret_play.append(played)
                ret_avg.append(averages)
                ret_gl.append(gl[0].game.date - timedelta(days=1))
            n_inputs = len(ret_play[0])# * 2
            n_hiddens = 1100
            n_outputs = len(ret_mins[0])
            learning_rate = 0.075

            nn = NeuralNet(n_inputs, n_hiddens, n_outputs, learning_rate)

            import numpy

            for i in range(5):
                for play, mins, avgs in zip(ret_play[:-1], ret_mins[:-1], ret_avg[:-1]):
                    inputs = play# + list((numpy.asfarray(avgs) / 40.0 * 0.99) + 0.01)
                    inputs = numpy.asfarray(inputs)
                    targets = (numpy.asfarray(mins) / 45.0 * 0.99) + 0.01
                    nn.train(inputs, targets)

            # import ipdb; ipdb.set_trace()
            # ret_play[-1][4] = 0

            out = nn.query(ret_play[-1]) * 45.0

            # print(out)
            # import ipdb; ipdb.set_trace()
            # pass

            table = Texttable(max_width=100)
            table.set_deco(Texttable.HEADER)
            table.add_row(('Player', 'Average', 'Predicted', 'Actual'))
            diff_avg = 0
            diff_pred = 0

            for player, predicted, actual, date in zip(players, out, ret_mins[-1], ret_gl):
                gl = player.game_logs_last_x_games(15, from_date=date)
                avg = player.average_minutes(game_logs=gl)
                if actual == 0:
                    avg = 0
                    predicted = 0
                table.add_row((
                    player.name, avg, predicted, actual
                ))
                if actual > 1:
                    diff_avg += abs(actual - avg)
                    diff_pred += abs(actual - predicted)

            table.add_row(('x', diff_avg, diff_pred, 'x'))

            print(table.draw())

            # vv = []
            # for v, k in zip(ret_mins, ret_play):
            #     vv.append(v + k)
            # print(vv)
