from django import forms
from django.views.generic import TemplateView

from basketball.models import Team
from basketball.utils.elo import ELO


class ELOForm(forms.Form):
    elo_1 = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control input-sm'}))
    elo_2 = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control input-sm'}))

    team_1 = forms.ModelChoiceField(
        Team.objects.all().order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control input-sm'}))
    team_2 = forms.ModelChoiceField(
        Team.objects.all().order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control input-sm'}))


class ELOView(TemplateView):

    template_name = 'elo.html'

    def get_context_data(self, **kwargs):
        context = super(ELOView, self).get_context_data(**kwargs)
        form = ELOForm(self.request.GET)

        if form.is_valid():
            elo_1 = form.cleaned_data['elo_1']
            elo_2 = form.cleaned_data['elo_2']

            team_1 = form.cleaned_data['team_1']
            team_2 = form.cleaned_data['team_2']

            if all((elo_1, elo_2)):
                diff = elo_1 - elo_2
            elif all((team_1, team_2)):
                diff = team_1.elo - team_2.elo
            else:
                diff = 0

            context['elo_diff'] = diff
            context['elo_point_spread'] = round(ELO.point_spread(diff), 1)
            context['elo_win_prob'] = round(ELO.win_probability(diff), 3) * 100.0

        context['form'] = form
        return context
