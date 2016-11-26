from collections import defaultdict

import simplejson as json
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django import forms
from scipy.stats.stats import pearsonr

from basketball.models import Player, Season, GameLog


class PlayerList(ListView):
    model = Player
    template_name = 'player_list.html'


class PlayerDetailFilters(forms.Form):
    season = forms.ModelChoiceField(
        queryset=Season.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control input-sm'}))


class PlayerDetail(DetailView):
    model = Player
    template_name = 'player_detail.html'

    def get_points_graph_data(self, game_logs):
        point_values = []
        for i, gl in enumerate(game_logs):
            point_values.append({
                'x': i + 1,
                'y': gl.draft_king_points,
                'game': str(gl.game),
                'elo_home': str(gl.game.home_team) + ' ' + str(gl.game.home_elo),
                'elo_away': str(gl.game.away_team) + ' ' + str(gl.game.away_elo),
            })
        return point_values

    def get_playtime_graph_data(self, game_logs):
        point_values = []
        for i, gl in enumerate(game_logs):
            point_values.append({
                'x': i + 1,
                'y': gl.minutes,
                'game': str(gl.game)
            })
        return point_values

    def get_graph_data(self, game_logs):
        data = [
            {
                'values': self.get_points_graph_data(game_logs),
                'key': 'points',
                'color': '#ff7f0e',
            },
            {
                'values': self.get_playtime_graph_data(game_logs),
                'key': 'playtime',
                'color': '#cc7ffe',
            },
        ]
        return data

    def get_game_logs(self, player):
        return player.gamelog_set.all().order_by('game__date')

    def get_context_data(self, **kwargs):
        context = super(PlayerDetail, self).get_context_data(**kwargs)
        player = context['object']
        game_logs = self.get_game_logs(player)

        page_filters = PlayerDetailFilters(self.request.GET)
        if page_filters.is_valid():

            season = page_filters.cleaned_data.get('season')
            if season:
                game_logs = game_logs.filter(game__season=season)

        context['filters'] = page_filters
        context['data'] = json.dumps(self.get_graph_data(game_logs))
        context['average_points'] = player.average_points(game_logs=game_logs)
        context['average_playtime'] = round(player.average_minutes(game_logs=game_logs), 2)
        context['average_pts_per_min'] = round(context['average_points'] / context['average_playtime'], 2)
        context['game_logs'] = game_logs

        # team_logs_by_game = player.current_team.game_logs_grouped_by_game(game_logs=GameLog.objects.filter(game__season=Season.objects.get(name='16')))
        # from numpy import cov
        # players = set()
        # for tlbg in team_logs_by_game:
        #     for foo in tlbg:
        #         players.add(foo.player.name)
        #
        # logs = defaultdict(list)
        # for tlbg in team_logs_by_game:
        #     for p in players:
        #         p_log = filter(lambda k: k.player.name == p, tlbg)
        #         if p_log:
        #             logs[p].append(p_log[0].minutes)
        #         else:
        #             logs[p].append(0)
        #
        # correlations = dict()
        # for k, v in logs.items():
        #     x = logs[player.name]
        #     y = v
        #
        #     # correlations[k] = pearsonr(x, y)
        #     correlations[k] = cov(x, y)
        # import ipdb; ipdb.set_trace()
        return context
