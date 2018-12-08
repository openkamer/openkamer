from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import TemplateView

from travel.models import Travel
from travel.filters import TravelFilter


class TravelsView(TemplateView):
    template_name = 'travel/travels.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        travels = Travel.objects.all().order_by('-date_begin')
        travel_filter = TravelFilter(self.request.GET, queryset=travels)
        travels_filtered = travel_filter.qs
        results_per_page = 99  # divisible by 3 for layout
        paginator = Paginator(travel_filter.qs, results_per_page)
        page = self.request.GET.get('page')
        try:
            travels = paginator.page(page)
        except PageNotAnInteger:
            travels = paginator.page(1)
        except EmptyPage:
            travels = paginator.page(paginator.num_pages)
        context['travels'] = travels
        context['filter'] = travel_filter
        context['n_results'] = travels_filtered.count()
        return context
