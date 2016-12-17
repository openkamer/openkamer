import datetime

from unidecode import unidecode

from django.views.generic import TemplateView

from parliament.models import PartyMember
from parliament.models import Parliament
from parliament.models import ParliamentMember
from parliament.models import PoliticalParty
from parliament import check


class PartiesView(TemplateView):
    template_name = 'parliament/parties.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parties = PoliticalParty.objects.all()
        parties = sorted(parties, key=lambda party: party.parliament_members_current.count(), reverse=True)
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

    def get_context_data(self, at_date, **kwargs):
        context = super().get_context_data(**kwargs)
        tweedekamer = Parliament.get_or_create_tweede_kamer()
        members = tweedekamer.get_members_at_date(at_date)
        context['members'] = members
        context['date'] = at_date
        return context


class ParliamentMembersCurrentView(ParliamentMembersView):
    def get_context_data(self, **kwargs):
        at_date = datetime.date.today()
        return super().get_context_data(at_date, **kwargs)


class ParliamentMembersAtDateView(ParliamentMembersView):
    def get_context_data(self, year, month, day, **kwargs):
        at_date = datetime.date(year=int(year), month=int(month), day=int(day))
        return super().get_context_data(at_date, **kwargs)


class PartyMembersCheckView(TemplateView):
    template_name = 'parliament/party_members_check.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_double_ids = []
        members = PartyMember.objects.filter(left__isnull=True)
        for member in members:
            members_same_person = PartyMember.objects.filter(person=member.person)
            if members_same_person.count() > 1:
                for member_same_person in members_same_person:
                    member_double_ids.append(member_same_person.id)
        context['members_double_current'] = PartyMember.objects.filter(id__in=member_double_ids)
        return context


class ParliamentMembersCheckView(TemplateView):
    template_name = 'parliament/members_check.html'

    def get_context_data(self, **kwargs):
        if not self.request.user.is_superuser:
            raise PermissionError("You need to be an admin to view this page.")
        context = super().get_context_data(**kwargs)
        start_date = datetime.date(year=2005, month=6, day=1)
        members_per_month = self.get_members_per_month(start_date)
        members = ParliamentMember.objects.all()
        members_overlap = []
        for member in members:
            members_overlap += member.check_overlap()
        overlap_ids = []
        for member in members_overlap:
            overlap_ids.append(member.id)
        parliament = Parliament.get_or_create_tweede_kamer()
        check_date = datetime.date.today()
        # check_date = datetime.date(year=2008, month=7, day=1)
        members_current = parliament.get_members_at_date(check_date)
        members_current_check = check.check_parliament_members_at_date(check_date)
        members_missing = check.get_members_missing(members_current, members_current_check)
        members_incorrect = check.get_members_incorrect(members_current, members_current_check)
        context['members'] = members
        context['members_current'] = sorted(members_current, key=lambda member: member.person.surname)
        context['members_current_missing'] = members_missing
        context['members_incorrect'] = sorted(members_incorrect, key=lambda member: member.person.surname)
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

