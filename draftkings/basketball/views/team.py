import simplejson as json
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django import forms

from basketball.models import Team, Season


class TeamList(ListView):
    model = Team
    template_name = 'team_list.html'

    def get_queryset(self):
        return Team.objects.all().order_by('name')


class TeamDetailFilters(forms.Form):
    season = forms.ModelChoiceField(
        queryset=Season.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control input-sm'}))


class TeamDetail(DetailView):
    model = Team
    template_name = 'team_detail.html'

    def get_points_graph_data(self, game_logs):
        point_values = []
        for i, game_log in enumerate(game_logs):
            point_values.append({
                'x': i + 1,
                'y': sum(gl.draft_king_points for gl in game_log),
                'game': str(game_log[0].game)
            })
        return point_values

    def get_playtime_graph_data(self, game_logs):
        point_values = []
        for i, game_log in enumerate(game_logs):
            point_values.append({
                'x': i + 1,
                'y': sum(gl.minutes for gl in game_log),
                'game': str(game_log[0].game)
            })
        return point_values

    def get_elo_graph_data(self, game_logs):
        point_values = []
        for i, game_log in enumerate(game_logs):
            point_values.append({
                'x': i + 1,
                'y': game_log[0].game.elo_for_team(game_log[0].team),
                'game': str(game_log[0].game)
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
            {
                'values': self.get_elo_graph_data(game_logs),
                'key': 'ELO',
                'color': '#007ffe',
            },
        ]
        return data

    def get_players(self, game_logs):
        players = set()
        for gl in game_logs:
            players.add(gl.player)
        return list(players)

    def get_context_data(self, **kwargs):
        context = super(TeamDetail, self).get_context_data(**kwargs)
        team = context['object']
        game_logs = team.game_logs()

        page_filters = TeamDetailFilters(self.request.GET)
        if page_filters.is_valid():

            season = page_filters.cleaned_data.get('season')
            if season:
                game_logs = game_logs.filter(game__season=season)

            context['season'] = season

        context['filters'] = page_filters
        context['data'] = json.dumps(self.get_graph_data(team.game_logs_grouped_by_game(game_logs=game_logs)))
        context['average_points'] = round(team.average_points(game_logs=game_logs), 2)
        context['average_playtime'] = round(team.average_playtime(game_logs=game_logs), 2)
        if context['average_playtime']:
            context['average_pts_per_min'] = round(context['average_points'] / context['average_playtime'], 2)
        else:
            context['average_pts_per_min'] = 0
        context['players'] = self.get_players(game_logs)
        return context
