from django.contrib import admin

from document.models import Document, Kamerstuk


class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'dossier_id',
        'raw_type',
        'date_published',
        'publisher',
        'raw_title',
    )


class KamerstukAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'document',
        'id_main',
        'id_sub',
        'type_short',
        'type_long',
        'document_date',
    )

    def document_date(self, obj):
        return obj.document.date_published


admin.site.register(Document, DocumentAdmin)
admin.site.register(Kamerstuk, KamerstukAdmin)