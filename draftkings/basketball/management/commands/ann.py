
from django.core.management.base import BaseCommand
from texttable import Texttable

from basketball.models import Team, Player
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

            players = Player.objects.filter(name__in=team.set_of_all_players()).order_by('name')
            game_logs = team.game_logs_grouped_by_game()

            ret_mins = []
            ret_play = []

            for gl in game_logs:
                minutes = []
                played = []
                for player in players:
                    l = filter(lambda k: k.player.pk == player.pk, gl)
                    val = sum([_.minutes for _ in l])
                    minutes.append(val)
                    played.append(0 if val == 0 else 1)
                ret_mins.append(minutes)
                ret_play.append(played)

            n_inputs = len(ret_play[0])
            n_hiddens = 100
            n_outputs = len(ret_mins[0])
            learning_rate = 0.1

            nn = NeuralNet(n_inputs, n_hiddens, n_outputs, learning_rate)

            import numpy

            for i in range(5):
                for play, mins in zip(ret_play[:-1], ret_mins[:-1]):
                    input = numpy.asfarray(play)
                    targets = (numpy.asfarray(mins) / 40.0 * 0.99) + 0.01
                    nn.train(input, targets)

            out = nn.query(ret_play[-1]) * 40

            # print(out)
            # import ipdb; ipdb.set_trace()
            # pass

            table = Texttable(max_width=100)
            table.set_deco(Texttable.HEADER)
            table.add_row(('Player', 'Average', 'Predicted', 'Actual'))
            for player, predicted, actual in zip(players, out, ret_mins[-1]):
                predicted = predicted if predicted > 4 else 0
                gl = player.game_logs_last_x_days(90)
                table.add_row((player.name, player.average_minutes(game_logs=gl), predicted, actual))

            print(table.draw())

            # vv = []
            # for v, k in zip(ret_mins, ret_play):
            #     vv.append(v + k)
            # print(vv)
