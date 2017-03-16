import json
import facebook

from django.conf import settings
from django.urls import reverse

from document.models import Kamervraag

graph = facebook.GraphAPI(access_token=settings.FACEBOOK_API_PAGE_TOKEN, version='2.7')


def get_kamervragen():
    print('get_kamervragen')
    fields = 'id,name,link'
    response = graph.request(path='openkamer/posts')
    ids = []
    for post in response['data']:
        post = graph.get_object(post['id'], fields=fields)
        if 'link' in post and 'kamervraag' in post['link']:
            ids.append(post['id'])


def create_submitters_string(submitters):
    submitters_string = ''
    counter = 1
    for submitter in submitters:
        submitters_string += str(submitter)
        if submitter.party:
            submitters_string += ' (' + str(submitter.party.name_short) + ')'
        if counter == (submitters.count()-1):
            submitters_string += ' en '
        elif counter < submitters.count():
            submitters_string += ', '
        counter += 1
    return submitters_string


def add_vragen_antwoorden_as_comments(post_id, kamervraag):
    for vraag in kamervraag.vragen:
        vraag_text = 'Vraag ' + str(vraag.nr) + ':\n'
        vraag_text += vraag.text
        # print(vraag_text)
        vraag_obj = graph.put_comment(object_id=post_id, message=vraag_text)
        antwoord_text = 'Antwoord:\n'
        antwoord_text += vraag.antwoord.text
        # print(antwoord_text)
        antwoord_obj = graph.put_comment(object_id=vraag_obj['id'], message=antwoord_text)


def post_kamervraag():
    kamervraag = Kamervraag.objects.filter(kamerantwoord__isnull=False)[14]

    attachment = {
        'name': 'Kamervraag - Open Kamer',
        'link': 'https://www.openkamer.org' + reverse('kamervraag', args=(kamervraag.vraagnummer,)),
        'caption': '',
        'description': '',
        # 'picture': ''

    }
    vragers_str = create_submitters_string(kamervraag.document.submitters)
    beantwoord_string = create_submitters_string(kamervraag.kamerantwoord.document.submitters)
    message = 'Antwoord op vragen over \'' + kamervraag.document.title_short + '\'.\n\n'
    message += 'Vragen door: ' + vragers_str + '\n'
    message += 'Antwoord van: ' + beantwoord_string + '\n'
    if kamervraag.document.footnote_set and kamervraag.document.footnote_set.all()[0].url:
        message += 'Over bericht: ' + kamervraag.document.footnote_set.all()[0].url
    print(message)
    response = graph.put_wall_post(profile_id=settings.FACEBOOK_PROFLE_ID, message=message, attachment=attachment)
    add_vragen_antwoorden_as_comments(response['id'], kamervraag)