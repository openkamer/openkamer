import os
import json

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.utils import timezone

from document.models import Dossier
from government.models import Government

from website import settings

from stats.views import get_example_plot_html


class HomeView(TemplateView):
    template_name = "website/index.html"
    context_object_name = "homepage"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class DatabaseDumpsView(TemplateView):
    template_name = "website/database_dumps.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backup_files = []
        for (dirpath, dirnames, filenames) in os.walk(settings.DBBACKUP_STORAGE_OPTIONS['location']):
            for file in filenames:
                if '.gitignore' in file or 'readme.txt' in file:
                    continue
                filepath = os.path.join(dirpath, file)
                size = os.path.getsize(filepath)
                backup_files.append({
                    'file': file,
                    'size': int(size)/1024/1024
                })
        context['backup_files'] = backup_files
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
