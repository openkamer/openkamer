from django.contrib import admin

from document.models import Document, Kamerstuk, Dossier


class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dossier_id',
        'title_short',
        'date_published',
        'publication_type',
        'submitter',
        'category',
        'publisher',
        'document_url',
        'title_full',
    )


class KamerstukAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'id_main',
        'id_sub',
        'type_short',
        'type_long',
        'document_date',
    )

    def document_date(self, obj):
        return obj.document.date_published


admin.site.register(Dossier)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Kamerstuk, KamerstukAdmin)