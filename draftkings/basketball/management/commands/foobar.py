from collections import OrderedDict

import datetime

from datetime import timedelta
from matplotlib import pyplot as plt

from django.core.management.base import BaseCommand
from itertools import groupby

from basketball.models import Team, Season, GameLog
import numpy as np
import matplotlib.cm as cm

from basketball.utils.dk_tools.salaries import SalaryFileManager


class Command(BaseCommand):

    help = ''

    def handle(self, *args, **options):
        # teams = Team.objects.all()
        season = Season.objects.get(name='16')
        # game_logs = GameLog.objects.filter(game__season=season,
        #                                    game__date__gte=datetime.datetime.now() - timedelta(days=30))

        salary_file = SalaryFileManager.salary_files()[-3]
        players = salary_file.from_db()
        players = filter(lambda x: x.gamelog_set.filter(game__date=salary_file.date()).count() > 0, players)
        players = filter(lambda x: x.current_team == players[0].current_team, players)

        colors = cm.rainbow(np.linspace(0, 1, len(players)))

        for color, player in zip(colors, players):

            game_logs = player.game_logs_for_season(season).order_by('game__date')

            x = mins = [0] + [gl.minutes for gl in game_logs]
            y = points = [0] + [gl.draft_king_points for gl in game_logs]

            plt.scatter(mins, points, color=color)

            # Add correlation line
            axes = plt.gca()
            m, b = np.polyfit(x, y, 1)
            X_plot = np.linspace(axes.get_xlim()[0], axes.get_xlim()[1], 100)

            plt.plot(X_plot, m * X_plot + b, '-', color=color)

        # plt.plot(np.unique(mins), np.poly1d(np.polyfit(mins, points, 1))(np.unique(mins)))
        plt.show()
        # players.sort(key=lambda x: str(x.gamelog_set.get(game__date=salary_file.date()).game))
        # centers = filter(lambda x: x.salary > 6000, players)
        # for g, val in groupby(players, lambda k: k.gamelog_set.get(game__date=salary_file.date()).game):
        #     val = sorted(val, key=lambda k: str(k.current_team))
        #
        #     for i, player in enumerate(val):
        #         gl = player.gamelog_set.get(game__date=salary_file.date())
        #         # if gl.minutes < 10:
        #         #     continue
        #
        #         gls = player.game_logs_last_x_days(30, from_date=salary_file.date() - timedelta(days=1))
        #         avg_ppm = player.average_ppm(game_logs=gls)
        #         avg_pts = player.average_points(game_logs=gls)
        #
        #         # if abs(gl.points_per_min - avg_ppm) < 0.15:
        #         #     continue
        #
        #         # plt.plot(i, gl.points_per_min - avg_ppm, marker='o')
        #         plt.plot(i, gl.draft_king_points - avg_pts, marker='D')
        #         plt.annotate(xy=(i, gl.draft_king_points - avg_pts), s='\n'.join([player.name, str(player.current_team)]))

        # for i, team in enumerate(teams[1:]):
        #     team_gls = team.game_logs_grouped_by_game(game_logs=game_logs)
        #
        #     dk_pts = 0
        #     for gl in team_gls:
        #         dk_pts += sum(_.field_goals_made for _ in gl)
        #
        #     plt.plot(i, dk_pts / len(team_gls), marker='o')
        #     plt.annotate(xy=(i, dk_pts / len(team_gls)), s=team.name)
        # plt.scatter(f1, f2, marker=marker, c=color)
        #     plt.axvline(linewidth=0.5, color='k')
        #     plt.axhline(linewidth=0.5, color='k')
        #     plt.show()
