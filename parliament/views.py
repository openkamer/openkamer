from django.views.generic import TemplateView

from parliament.models import PoliticalParty, ParliamentMember


class PartiesView(TemplateView):
    template_name = 'parliament/parties.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parties = PoliticalParty.objects.all()
        context['parties'] = parties
        return context


class ParliamentMembersView(TemplateView):
    template_name = 'parliament/members.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        members = ParliamentMember.objects.all()
        context['members'] = members
        return context
