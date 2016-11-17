
import simplejson as json
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django import forms

from basketball.models import Player, Season


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
                'game': str(gl.game)
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
        return context
