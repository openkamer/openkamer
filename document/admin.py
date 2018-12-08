from django.contrib import admin

from document.models import BesluitenLijst
from document.models import Dossier
from document.models import Document
from document.models import CategoryDossier
from document.models import CategoryDocument
from document.models import Kamerstuk
from document.models import Kamervraag
from document.models import Kamerantwoord
from document.models import KamervraagMededeling
from document.models import Submitter
from document.models import Vote
from document.models import VoteParty
from document.models import VoteIndividual
from document.models import Voting


class DossierAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dossier_id',
        'title',
        'decision',
        'status',
        'date_updated',
    )


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug'
    )


class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dossier',
        'document_id',
        'title_short',
        'date_published',
        'publication_type',
        'publisher',
        'document_url',
        'title_full',
        'date_updated'
    )
    list_filter = ('publication_type',)


class KamerstukAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'id_main',
        'id_main_extra',
        'id_sub',
        'type',
        'type_short',
        'type_long',
        'document_date',
        'original_id',
        'date_updated',
        'dossier_ids_related'
    )
    list_filter = ('type',)

    def document_date(self, obj):
        return obj.document.date_published


class BesluitenLijstAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'date_published',
        'commission',
        'activity_id',
        'url',
    )


class KamervraagAdmin(admin.ModelAdmin):
    list_display = (
        'vraagnummer', 'document',
    )


class KamerantwoordAdmin(admin.ModelAdmin):
    list_display = (
        'vraagnummer', 'document',
    )


class KamervraagMededelingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'document', 'vraagnummer', 'kamervraag',
    )


class SubmitterAdmin(admin.ModelAdmin):
    list_display = ('id', 'person', 'party_slug', 'document_id')


class VotingAdmin(admin.ModelAdmin):
    list_display = ('dossier', 'result', 'date', 'is_dossier_voting', 'kamerstuk')


class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'voting', 'decision', 'number_of_seats', 'details')


class VotePartyAdmin(admin.ModelAdmin):
    list_display = ('id', 'voting', 'party', 'decision', 'number_of_seats', 'details')


class VoteIndividualAdmin(admin.ModelAdmin):
    list_display = ('id', 'voting', 'parliament_member', 'decision', 'number_of_seats', 'details')


admin.site.register(CategoryDossier, CategoryAdmin)
admin.site.register(CategoryDocument, CategoryAdmin)
admin.site.register(Dossier, DossierAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Kamerstuk, KamerstukAdmin)
admin.site.register(Submitter, SubmitterAdmin)
admin.site.register(Kamervraag, KamervraagAdmin)
admin.site.register(Kamerantwoord, KamerantwoordAdmin)
admin.site.register(KamervraagMededeling, KamervraagMededelingAdmin)

admin.site.register(BesluitenLijst, BesluitenLijstAdmin)

admin.site.register(Vote, VoteAdmin)
admin.site.register(VoteParty, VotePartyAdmin)
admin.site.register(VoteIndividual, VoteIndividualAdmin)
admin.site.register(Voting, VotingAdmin)
