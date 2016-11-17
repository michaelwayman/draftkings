
import simplejson as json
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django import forms

from basketball.models import Player, Team, GameLog, Game


class GameList(ListView):
    model = Player
    template_name = 'player_list.html'


class GameDetail(DetailView):
    model = Game
    template_name = 'game_detail.html'

    # def get_points_graph_data(self, stats):
    #     point_values = []
    #     for i, stat in enumerate(stats):
    #         point_values.append({
    #             'x': i + 1,
    #             'y': stat.draft_king_points,
    #             'game': str(stat.game)
    #         })
    #     return point_values
    #
    # def get_playtime_graph_data(self, stats):
    #     point_values = []
    #     for i, stat in enumerate(stats):
    #         point_values.append({
    #             'x': i + 1,
    #             'y': stat.minutes,
    #             'game': str(stat.game)
    #         })
    #     return point_values

    # def get_graph_data(self, stats):
    #     data = [
    #         {
    #             'values': self.get_points_graph_data(stats),
    #             'key': 'points',
    #             'color': '#ff7f0e',
    #         },
    #         {
    #             'values': self.get_playtime_graph_data(stats),
    #             'key': 'playtime',
    #             'color': '#cc7ffe',
    #         },
    #     ]
    #     return data

    def get_stats(self, game):
        class Foo(object):
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        stats = list(game.gamelog_set.all())
        players = set(s.player for s in stats)
        for g in [game.home_team, game.away_team]:
            pls = g.players.all()
            for p in pls:
                if p not in players:
                    stats.append(Foo(player=p, minutes=0, team=g, draft_king_points=0, points_per_min=0))
        return stats

    def get_context_data(self, **kwargs):
        context = super(GameDetail, self).get_context_data(**kwargs)
        game = context['object']
        stats = self.get_stats(game)

        # context['data'] = json.dumps(self.get_graph_data(stats))
        # context['average_points'] = player.average_points(stats=stats)
        # context['average_playtime'] = round(player.average_minutes(stats=stats), 2)
        # context['average_pts_per_min'] = round(context['average_points'] / context['average_playtime'], 2)
        context['stats'] = stats
        return context
