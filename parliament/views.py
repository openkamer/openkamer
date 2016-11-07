import datetime

from django.views.generic import TemplateView

from parliament.models import Parliament
from parliament.models import ParliamentMember
from parliament.models import PoliticalParty


class PartiesView(TemplateView):
    template_name = 'parliament/parties.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parties = PoliticalParty.objects.all()
        context['parties'] = parties
        return context


class PartyView(TemplateView):
    template_name = 'parliament/party.html'

    def get_context_data(self, slug, **kwargs):
        context = super().get_context_data(**kwargs)
        party = PoliticalParty.objects.get(slug=slug)
        context['party'] = party
        return context


class ParliamentMembersView(TemplateView):
    template_name = 'parliament/members.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        members = ParliamentMember.objects.all()
        context['members'] = members
        return context


class ParliamentMembersCheckView(TemplateView):
    template_name = 'parliament/members_check.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date = datetime.date(year=2000, month=1, day=1)
        # members_per_month = self.get_members_per_month(start_date)
        members = ParliamentMember.objects.all()
        context['members'] = members
        return context

    @staticmethod
    def get_members_per_month(start_date):
        start_date = datetime.date(year=2000, month=1, day=1)
        current_date = start_date
        parliament = Parliament.get_or_create_tweede_kamer()
        members_per_month = []
        while current_date < datetime.date.today():
            members = parliament.get_members_at_date(current_date)
            members_per_month.append({
                'date': current_date,
                'members': members,
            })
            print(current_date)
            print(len(members))
            current_date += datetime.timedelta(days=31)
        return members_per_month
