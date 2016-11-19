from django import forms
from django.shortcuts import render
from django.views.generic.edit import FormView
from basketball.utils.dk_tools.salaries import SalaryFileManager

from basketball.models import Player, GameLog


class LineupForm(forms.Form):
    lineup = forms.CharField(widget=forms.Textarea, required=False)
    contest = forms.ChoiceField(choices=enumerate(SalaryFileManager.salary_files()))


class CustomLineupView(FormView):

    template_name = 'custom_lineup.html'
    form_class = LineupForm

    def players_from_lineup(self, lineup):
        if lineup:
            players = lineup.split(',')
            players = [player.strip() for player in players]
            players = [player for player in players if player]
            return Player.objects.filter(name__in=players)
        else:
            return Player.objects.all()

    def form_valid(self, form):
        lineup = form.cleaned_data['lineup']
        contest_id = form.cleaned_data['contest']

        players = self.players_from_lineup(lineup)
        contest = SalaryFileManager.salary_files()[int(contest_id)]
        date = contest.date()

        game_logs = []
        for player in players:
            try:
                ps = player.gamelog_set.get(game__date=date)
                ps.expected_points = player.estimated_points(date=date)
                game_logs.append(ps)
            except GameLog.DoesNotExist:
                ps = Foo()
                ps.expected_points = player.estimated_points(date=date)
                ps.player = player
                ps.draft_king_points = 0
                ps.minutes = 0
                game_logs.append(ps)
        return render(
            self.request,
            self.template_name,
            self.get_context_data(
                game_logs=game_logs,
                total_points=sum(stat.draft_king_points for stat in game_logs),
                total_points_avg=sum(stat.player.average_points(stat.player.game_logs_before_date(date)) for stat in game_logs),
                total_points_predicted=sum(stat.player.estimated_points(date=date) for stat in game_logs),
                total_playtime=sum(stat.minutes for stat in game_logs),
                total_playtime_avg=sum(stat.player.average_minutes(stat.player.game_logs_before_date(date)) for stat in game_logs),
            )
        )


class Foo(object):
    pass
