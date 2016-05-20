from django.db import models

import scraper.documents


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
    id_main = models.CharField(max_length=40, blank=True)
    id_sub = models.CharField(max_length=40, blank=True)
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


def create_or_update_dossier(dossier_id):
    print('create or update dossier')
    dossiers = Dossier.objects.filter(dossier_id=dossier_id)
    if dossiers:
        dossier = dossiers[0]
    else:
        dossier = Dossier.objects.create(dossier_id=dossier_id)
    search_results = scraper.documents.search_politieknl_dossier(dossier_id)
    for result in search_results:
        print('create document')
        document = Document.objects.create(
            dossier=dossier,
            raw_type=result['type'],
            raw_title=result['title'],
            publisher=result['publisher'],
            date_published=result['published_date'],
            document_url=result['page_url'],
        )

        if 'Kamerstuk' in result['type']:
            print('create kamerstuk')
            # print(result['type'])
            items = result['type'].split(' ')
            # print(items)
            title_parts = result['title'].split(';')
            type_short = ''
            type_long = ''
            if len(title_parts) > 2:
                type_short = title_parts[1].strip()
                type_long = title_parts[2].strip()
            if "Bijlage" in result['type']:
                print('BIJLAGE')
                id_main = str(items[4])
                id_sub = str(items[6])
                type_short = 'Bijlage'
                type_long = 'Bijlage'
            else:
                id_main = str(items[2])
                id_sub = str(items[4])
            Kamerstuk.objects.create(
                document=document,
                id_main=id_main,
                id_sub=id_sub,
                type_short=type_short,
                type_long=type_long,
            )
    return dossier
