from django.db import models

import scraper.documents


class Dossier(models.Model):
    dossier_id = models.CharField(max_length=100, blank=True, unique=True)

    def __str__(self):
        return str(self.dossier_id)

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
    document_id = models.CharField(max_length=200, blank=True)
    title_full = models.CharField(max_length=500)
    title_short = models.CharField(max_length=200)
    publication_type = models.CharField(max_length=200)
    submitter = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    date_published = models.DateField(blank=True, null=True)

    def title(self):
        return self.title_short

    def document_url(self):
        return 'https://zoek.officielebekendmakingen.nl/' + str(self.document_id) + '.html'

    def __str__(self):
        return self.title_short

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
        print('create document for results:')

        # skip documents of some types and/or sources, no models implemente yet
        # TODO: handle all document types
        if 'Agenda' in result['type'].split(' ')[0]:
            print('WARNING: Agenda, skip for now')
            continue
        if 'Staatscourant' in result['type']:
            print('WARNING: Staatscourant, skip for now')
            continue

        document_id = scraper.documents.get_document_id(result['page_url'])
        if not document_id:
            print('WARNING: No document id found, will not create document')
            continue

        metadata = scraper.documents.get_metadata(document_id)

        if metadata['date_published']:
            date_published = metadata['date_published']
        else:
            date_published = result['date_published']

        document = Document.objects.create(
            dossier=dossier,
            document_id=document_id,
            title_full=metadata['title_full'],
            title_short=metadata['title_short'],
            publication_type=metadata['publication_type'],
            submitter=metadata['submitter'],
            category=metadata['category'],
            publisher=metadata['publisher'],
            date_published=date_published,
        )

        if metadata['is_kamerstuk']:
            print('create kamerstuk')
            # print(items)
            title_parts = metadata['title_full'].split(';')
            type_short = ''
            type_long = ''
            if len(title_parts) > 2:
                type_short = title_parts[1].strip()
                type_long = title_parts[2].strip()
            if "Bijlage" in result['type']:
                print('BIJLAGE')
                type_short = 'Bijlage'
                type_long = 'Bijlage'
            Kamerstuk.objects.create(
                document=document,
                id_main=dossier_id,
                id_sub=metadata['id_sub'],
                type_short=type_short,
                type_long=type_long,
            )
    return dossier
