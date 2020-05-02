import os
import json
import datetime

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.template.loader import render_to_string

from person.models import Person
from document.models import Dossier
from document.models import Submitter
from document.models import Kamervraag
from document.models import Kamerstuk
from document.views import TimelineKamervraagItem
from document.views import TimelineKamerstukItem
from government.models import Government

from website import settings

from stats.views import get_example_plot_html


class HomeView(TemplateView):
    template_name = "website/index.html"
    context_object_name = "homepage"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ContactView(TemplateView):
    template_name = "website/contact.html"
    context_object_name = "contact"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_email'] = settings.CONTACT_EMAIL
        return context


def create_timeline_date(date):
    return {
        'year': date.year,
        'month': date.month,
        'day': date.day
    }


def get_dossier_timeline_json(request):
    governments = Government.objects.all()
    eras = []
    for government in governments:
        if government.date_dissolved:
            end_date = government.date_dissolved
        else:
            end_date = timezone.now()
        text = {
            'headline': government.name,
            'text': government.name
        }
        era = {
            'start_date': create_timeline_date(government.date_formed),
            'end_date': create_timeline_date(end_date),
            'text': text
        }
        eras.append(era)
    events = []
    if 'dossier_pk' in request.GET:
        dossier = Dossier.objects.get(id=request.GET['dossier_pk'])
        for kamerstuk in dossier.kamerstukken:
            text = {
                'headline': kamerstuk.type_short,
                'text': kamerstuk.type_long
            }
            event = {
                'start_date': create_timeline_date(kamerstuk.document.date_published),
                'text': text
            }
            events.append(event)
    timeline_info = {
        'events': events,
        'eras': eras
    }
    timeline_json = json.dumps(timeline_info, sort_keys=True, indent=4)
    # print(timeline_json)
    return HttpResponse(timeline_json, content_type='application/json')


class PlotExampleView(TemplateView):
    template_name = "website/plot_examples.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plot_html'] = mark_safe(get_example_plot_html())
        return context


class DatabaseDumpsView(TemplateView):
    template_name = "website/database_dumps.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backup_files = self.get_files(settings.DBBACKUP_STORAGE_OPTIONS['location'])
        context['backup_files'] = sorted(backup_files, key=lambda backup: backup['datetime_created'], reverse=True)
        return context

    @staticmethod
    def get_files(path):
        files = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            for file in filenames:
                if '.gitignore' in file or 'readme.txt' in file:
                    continue
                filepath = os.path.join(dirpath, file)
                size = os.path.getsize(filepath)
                datetime_created = os.path.getctime(filepath)
                files.append({
                    'file': file,
                    'size': int(size)/1024/1024,
                    'datetime_created': datetime.datetime.fromtimestamp(datetime_created)
                })
        return files


class CSVExportsView(TemplateView):
    template_name = "website/csv_exports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        files = DatabaseDumpsView.get_files(settings.CSV_EXPORT_PATH)
        context['files'] = sorted(files, key=lambda file: file['datetime_created'], reverse=True)
        return context


class PersonTimelineView(TemplateView):
    template_name = "website/items/person_timeline.html"

    @staticmethod
    def get_timeline_items(person, year=None):
        if year:
            year = int(year)
            submitters = Submitter.objects.filter(person=person, document__date_published__range=[datetime.date(year=year, day=1, month=1), datetime.date(year=year, day=31, month=12)])
        else:
            submitters = Submitter.objects.filter(person=person)
        submitter_ids = list(submitters.values_list('id', flat=True))
        timeline_items = []
        kamervragen = Kamervraag.objects.filter(document__submitter__in=submitter_ids).select_related('document', 'kamerantwoord')
        for kamervraag in kamervragen:
            timeline_items.append(TimelineKamervraagItem(kamervraag))
        kamerstukken = Kamerstuk.objects.filter(document__submitter__in=submitter_ids).select_related('document')
        for kamerstuk in kamerstukken:
            timeline_items.append(TimelineKamerstukItem(kamerstuk))
        timeline_items = sorted(timeline_items, key=lambda items: items.date, reverse=True)
        return timeline_items

    def get_context_data(self, slug, year, **kwargs):
        year = int(year)
        context = super().get_context_data(**kwargs)
        person = Person.objects.get(slug=slug)
        timeline_items = []
        has_next = True
        while len(timeline_items) == 0:
            timeline_items = PersonTimelineView.get_timeline_items(person, year)
            if timeline_items:
                break
            if year < 1996:
                has_next = False
                break
            year -= 1
        if year == datetime.date.today().year:
            next_year = None
        else:
            next_year = year + 1
        context['timeline_items'] = timeline_items
        context['person'] = person
        context['is_person_timeline'] = True
        context['previous_year'] = year - 1
        context['next_year'] = next_year
        context['has_next'] = has_next
        return context


def get_person_timeline_html(request):
    person = Person.objects.get(id=request.GET['person_id'])
    year = int(request.GET['year'])
    timeline_items = PersonTimelineView.get_timeline_items(person, year)
    if year == datetime.date.today().year:
        next_year = None
    else:
        next_year = year + 1
    html = render_to_string('website/items/person_timeline.html', {
        'timeline_items': timeline_items,
        'person': person,
        'is_person_timeline': True,
        'previous_year': year-1,
        'year': next_year,
        'has_next': True
    })
    response = json.dumps({'html': html})
    return HttpResponse(response, content_type='application/json')
