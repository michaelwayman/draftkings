from django.views.generic import ListView, DetailView

from basketball.models import Contest


class ContestListView(ListView):

    model = Contest
    template_name = 'contest_list.html'


class ContestDetailView(DetailView):
    model = Contest
    template_name = 'contest_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ContestDetailView, self).get_context_data(**kwargs)
        context['payouts'] = context['object'].contestpayout_set.all().order_by('start')
        return context
