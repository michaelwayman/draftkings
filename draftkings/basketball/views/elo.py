from django import forms
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

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


class ELOView(FormView):

    template_name = 'elo.html'
    form_class = ELOForm

    def form_valid(self, form):
        context = self.get_context_data()
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

        return render(self.request, self.template_name, context)
