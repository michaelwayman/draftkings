
from matplotlib import pyplot as plt

from django.core.management.base import BaseCommand

from basketball.models import Season, GameLog, Game
import numpy as np
import matplotlib.cm as cm


class Command(BaseCommand):

    help = ''

    def handle(self, *args, **options):

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
