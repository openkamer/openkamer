import datetime

from unidecode import unidecode

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
        start_date = datetime.date(year=2005, month=6, day=1)
        members_per_month = self.get_members_per_month(start_date)
        members = ParliamentMember.objects.filter()
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
        members_current_check = check_parliament_members_at_date(check_date)
        members_missing = []
        for member_check in members_current_check:
            found = False
            member_check_name = unidecode(member_check['name'])
            member_check_forename = unidecode(member_check['forename'])
            for member in members_current:
                member_name = unidecode(member.person.surname_including_prefix())
                if member_check_name == member_name and member_check_forename == unidecode(member.person.forename):
                    found = True
                    break
            if not found:
                members_missing.append(member_check['initials'] + ' ' + member_check['name'] + ' (' + member_check['forename'] + ')')
                # print(member_check['name'])
        members_wrong = []
        for member in members_current:
            found = False
            member_name = unidecode(member.person.surname_including_prefix())
            member_forename = unidecode(member.person.forename)
            for member_check in members_current_check:
                member_check_name = unidecode(member_check['name'])
                member_check_forename = unidecode(member_check['forename'])
                if member_check_name == member_name and member_check_forename == member_forename:
                    found = True
                    break
            if not found:
                members_wrong.append(member)
                # print(member.person.fullname())
        context['members'] = members
        context['members_current'] = sorted(members_current, key=lambda member: member.person.surname)
        context['members_current_missing'] = members_missing
        context['members_current_wrong'] = sorted(members_wrong, key=lambda member: member.person.surname)
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
