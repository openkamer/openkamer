from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import TemplateView

from gift.models import Gift
from gift.filters import GiftFilter


class GiftsView(TemplateView):
    template_name = 'gift/gifts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gifts = Gift.objects.all().order_by('-date')
        gift_filter = GiftFilter(self.request.GET, queryset=gifts)
        gifts_filtered = gift_filter.qs
        results_per_page = 99  # divisible by 3 for layout
        paginator = Paginator(gift_filter.qs, results_per_page)
        page = self.request.GET.get('page')
        try:
            gifts = paginator.page(page)
        except PageNotAnInteger:
            gifts = paginator.page(1)
        except EmptyPage:
            gifts = paginator.page(paginator.num_pages)
        sum_euro, average = Gift.calc_sum_average(gifts_filtered)
        context['gifts'] = gifts
        context['filter'] = gift_filter
        context['n_results'] = gifts_filtered.count()
        context['value_total_euro'] = int(sum_euro)
        context['value_average_euro'] = int(average)
        return context
