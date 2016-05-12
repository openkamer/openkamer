
import logging
logger = logging.getLogger(__name__)

from django.views.generic import TemplateView

from voting.models import Bill
from voting.models import Member


class HomeView(TemplateView):
    template_name = "website/index.html"
    context_object_name = "homepage"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        return context


class BillsView(TemplateView):
    template_name = "website/bills.html"
    context_object_name = "bills"

    def get_context_data(self, **kwargs):
        context = super(BillsView, self).get_context_data(**kwargs)

        bills = Bill.objects.all()
        for bill in bills:
            bill.votes = bill.get_votes()
        context['bills'] = bills
        return context


class MembersView(TemplateView):
    template_name = "website/members.html"
    context_object_name = "members"

    def get_context_data(self, **kwargs):
        context = super(MembersView, self).get_context_data(**kwargs)

        members = Member.objects.all()
        context['members'] = members
        return context