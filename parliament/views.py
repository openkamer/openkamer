import datetime

from django.views.generic import TemplateView

from parliament.models import Parliament
from parliament.models import ParliamentMember
from parliament.models import PoliticalParty
from parliament.check import check_parliament_members_at_date


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
        start_date = datetime.date(year=2010, month=1, day=1)
        members_per_month = self.get_members_per_month(start_date)
        members = ParliamentMember.objects.all()
        members_overlap = []
        for member in members:
            members_overlap += member.check_overlap()
        overlap_ids = []
        for member in members_overlap:
            overlap_ids.append(member.id)
        context['members'] = members
        parliament = Parliament.get_or_create_tweede_kamer()
        members_current = parliament.get_members_at_date(datetime.date.today())
        members_current_check = check_parliament_members_at_date(datetime.date.today())
        members_missing = []
        for member_check in members_current_check:
            found = False
            for member in members_current:
                if member_check['name'] == member.person.surname_including_prefix():
                    found = True
                    break
            if not found:
                members_missing.append(member_check['initials'] + ' ' + member_check['name'])
                print(member_check['name'])
        members_wrong = []
        for member in members_current:
            found = False
            for member_check in members_current_check:
                if member_check['name'] == member.person.surname_including_prefix():
                    found = True
                    break
            if not found:
                members_wrong.append(member)
                print(member.person.fullname())
        context['members_current'] = members_current
        context['members_current_wrong'] = members_wrong
        context['members_current_missing'] = members_missing
        context['members_overlap'] = ParliamentMember.objects.filter(pk__in=overlap_ids).distinct()
        context['members_per_month'] = members_per_month
        return context

    @staticmethod
    def get_members_per_month(start_date):
        current_date = start_date
        parliament = Parliament.get_or_create_tweede_kamer()
        members_per_month = []
        while current_date < datetime.date.today():
            members = parliament.get_members_at_date(current_date)
            members_per_month.append({
                'date': current_date,
                'members': members,
            })
            current_date += datetime.timedelta(days=31)
        current_date = datetime.date.today()
        members = parliament.get_members_at_date(current_date)
        members_per_month.append({
            'date': current_date,
            'members': members,
        })
        return members_per_month
