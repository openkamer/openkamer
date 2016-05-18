from django.db import models


class Document(models.Model):
    dossier_id = models.CharField(max_length=100, blank=True)
    raw_title = models.CharField(max_length=500)
    raw_type = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    date_published = models.DateField(blank=True, null=True)
    document_url = models.URLField(unique=True, blank=True)

    def __str__(self):
        return self.raw_type

    class Meta:
        ordering = ['-date_published']


class Kamerstuk(models.Model):
    document = models.ForeignKey(Document)
    id_main = models.IntegerField(blank=True, null=True)
    id_sub = models.IntegerField(blank=True, null=True)
    type_short = models.CharField(max_length=40, blank=True)
    type_long = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return str(self.id_main) + '.' + str(self.id_sub) + ' ' + str(self.type_long)

    class Meta:
        verbose_name_plural = 'Kamerstukken'
