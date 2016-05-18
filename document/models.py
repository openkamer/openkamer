from django.db import models


class Dossier(models.Model):
    dossier_id = models.CharField(max_length=100, blank=True, unique=True)

    def __str__(self):
        return 'Dossier model with id: ' + str(self.dossier_id)

    def documents(self):
        return Document.objects.filter(dossier=self)

    def kamerstukken(self):
        return Kamerstuk.objects.filter(document__dossier=self)

    def title(self):
        kamerstukken = self.kamerstukken()
        titles = {}
        for stuk in kamerstukken:
            title = stuk.document.title()
            if title in titles:
                titles[title] += 1
            else:
                titles[title] = 0
        max_titles = 0
        title = 'undefined'
        for key, value in titles.items():
            if value > max_titles:
                title = key
        return title


class Document(models.Model):
    dossier = models.ForeignKey(Dossier, blank=True, null=True)
    raw_title = models.CharField(max_length=500)
    raw_type = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    date_published = models.DateField(blank=True, null=True)
    document_url = models.URLField(unique=True, blank=True)

    def title(self):
        return self.raw_title.split(';')[0]

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

    def visible(self):
        if self.type_short == 'Koninklijke boodschap':
            return False
        return True

    def voorstelwet(self):
        if self.type_short == 'Voorstel van wet':
            return True
        return False

    class Meta:
        verbose_name_plural = 'Kamerstukken'
        ordering = ['id_sub']
